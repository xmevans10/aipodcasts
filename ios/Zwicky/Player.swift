import AVFoundation
import MediaPlayer
import SwiftUI
import UIKit

/// Only the visible transport and read-along views observe this frequent value.
@MainActor final class PlaybackClock: ObservableObject {
    @Published var position = 0.0
}

@MainActor final class AudioPlayer: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    @Published var story: Story?
    @Published var playing = false
    let clock = PlaybackClock()
    var position: Double {
        get { clock.position }
        set { clock.position = newValue }
    }
    @Published var duration = 1.0
    @Published var rate: Float = 1
    @Published var message: String?
    @Published private(set) var listening = ListeningState()
    @Published var sleepUntil: Date?
    /// Set to present the full player sheet from anywhere.
    @Published var isPlayerPresented = false
    var onStarted: ((Story) -> Void)?
    private var catalog: [String: Story] = [:]
    private var feed: [String] = []
    private var history: [String] = []
    var queuedStories: [Story] { listening.queue.compactMap { catalog[$0] } }
    /// Feed order, with the current story and any queued extras appended. Drives the player pager.
    var playlist: [Story] {
        var ids = feed
        for id in ([story?.id] + listening.queue).compactMap({ $0 }) where !ids.contains(id) { ids.append(id) }
        return ids.compactMap { catalog[$0] }
    }
    func playlistIndex(of id: String?) -> Int? {
        guard let id else { return nil }
        return playlist.firstIndex { $0.id == id }
    }
    private var activeUtterance: AVSpeechUtterance?
    private let speech = AVSpeechSynthesizer()
    private var dialogue: [DialogueTurn] = []
    private var dialogueIndex = 0
    private var inDialogue = false
    private var player: AVPlayer?
    private var observer: Any?
    private var endObserver: NSObjectProtocol?
    private var sleepTask: Task<Void, Never>?
    private var lastCheckpointAt = 0.0
    private var lastTick: Date?
    private var pendingListenDay: String?
    private var pendingListenSeconds = 0.0
    private var interruptionObserver: NSObjectProtocol?
    private var routeObserver: NSObjectProtocol?
    private var wasPlayingBeforeInterruption = false
    private var artworkCache: [String: MPMediaItemArtwork] = [:]
    private var lastSyncedSecond = -1
    /// Seconds of real audio listened, keyed by local day ("yyyy-MM-dd").
    @Published private(set) var listenedSeconds: [String: Double] = UserDefaults.standard.dictionary(forKey: "listenedSeconds") as? [String: Double] ?? [:]
    var isPreview: Bool { story?.audioURL == nil }
    var hasLoadedAudio: Bool { player != nil }
    override init() {
        super.init(); speech.delegate = self
        if let data = UserDefaults.standard.data(forKey: "listeningState"), let stored = try? JSONDecoder().decode(ListeningState.self, from: data) { listening = stored }
        configureRemoteCommands()
        observeAudioSession()
    }

    /// Lock-screen and Control Center controls, wired to the queue and transport.
    private func configureRemoteCommands() {
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.addTarget { [weak self] _ in Task { @MainActor in self?.resume() }; return .success }
        center.pauseCommand.addTarget { [weak self] _ in Task { @MainActor in self?.pause() }; return .success }
        center.togglePlayPauseCommand.addTarget { [weak self] _ in Task { @MainActor in self?.toggle() }; return .success }
        center.nextTrackCommand.addTarget { [weak self] _ in Task { @MainActor in self?.next() }; return .success }
        center.previousTrackCommand.addTarget { [weak self] _ in Task { @MainActor in self?.previous() }; return .success }
        center.skipForwardCommand.preferredIntervals = [NSNumber(value: 15)]
        center.skipBackwardCommand.preferredIntervals = [NSNumber(value: 15)]
        center.skipForwardCommand.addTarget { [weak self] _ in Task { @MainActor in self?.skip(by: 15) }; return .success }
        center.skipBackwardCommand.addTarget { [weak self] _ in Task { @MainActor in self?.skip(by: -15) }; return .success }
        center.changePlaybackPositionCommand.addTarget { [weak self] event in
            let time = (event as? MPChangePlaybackPositionCommandEvent)?.positionTime
            Task { @MainActor in if let time { self?.seek(time) } }
            return .success
        }
    }

    private func observeAudioSession() {
        let session = AVAudioSession.sharedInstance()
        interruptionObserver = NotificationCenter.default.addObserver(forName: AVAudioSession.interruptionNotification, object: session, queue: .main) { [weak self] note in
            Task { @MainActor in self?.handleInterruption(note) }
        }
        routeObserver = NotificationCenter.default.addObserver(forName: AVAudioSession.routeChangeNotification, object: session, queue: .main) { [weak self] note in
            Task { @MainActor in self?.handleRouteChange(note) }
        }
    }

    /// Pause for calls/Siri and resume only when the system says it is safe.
    private func handleInterruption(_ note: Notification) {
        guard let raw = note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        switch type {
        case .began:
            wasPlayingBeforeInterruption = playing
            if playing { pause() }
        case .ended:
            let rawOptions = note.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt ?? 0
            if AVAudioSession.InterruptionOptions(rawValue: rawOptions).contains(.shouldResume), wasPlayingBeforeInterruption { resume() }
            wasPlayingBeforeInterruption = false
        default:
            break
        }
    }

    /// Stop when headphones are unplugged or a Bluetooth route drops.
    private func handleRouteChange(_ note: Notification) {
        guard let raw = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
              let reason = AVAudioSession.RouteChangeReason(rawValue: raw) else { return }
        if reason == .oldDeviceUnavailable, playing { pause() }
    }

    /// Refresh lock-screen metadata: title, show, elapsed time, duration and rate.
    func updateNowPlaying() {
        guard let story else { MPNowPlayingInfoCenter.default().nowPlayingInfo = nil; return }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: story.title,
            MPMediaItemPropertyArtist: "Zwicky · \(story.host.name)",
            MPMediaItemPropertyAlbumTitle: story.show.title,
            MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaType.audio.rawValue,
        ]
        if !isPreview {
            info[MPNowPlayingInfoPropertyElapsedPlaybackTime] = position
            info[MPMediaItemPropertyPlaybackDuration] = duration
            info[MPNowPlayingInfoPropertyPlaybackRate] = playing ? Double(rate) : 0
        }
        if let art = artwork(for: story.show) { info[MPMediaItemPropertyArtwork] = art }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func artwork(for show: Show) -> MPMediaItemArtwork? {
        if let cached = artworkCache[show.id] { return cached }
        let size = CGSize(width: 600, height: 600)
        let image = UIGraphicsImageRenderer(size: size).image { context in
            let colors = [UIColor(show.light).cgColor, UIColor(show.mid).cgColor, UIColor(show.dark).cgColor] as CFArray
            if let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(), colors: colors, locations: [0, 0.55, 1]) {
                context.cgContext.drawLinearGradient(gradient, start: .zero, end: CGPoint(x: size.width, y: size.height), options: [])
            }
            let style = NSMutableParagraphStyle(); style.alignment = .left
            let attributes: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 54, weight: .bold),
                .foregroundColor: UIColor.white,
                .paragraphStyle: style,
            ]
            let label = show.title + "\n" + show.host.name
            (label as NSString).draw(in: CGRect(x: 48, y: size.height - 232, width: size.width - 96, height: 184), withAttributes: attributes)
        }
        let artwork = MPMediaItemArtwork(boundsSize: size) { _ in image }
        artworkCache[show.id] = artwork
        return artwork
    }

    func skip(by seconds: Double) { seek(position + seconds) }

    /// Lock-screen "previous": restart the episode unless we are already near its start.
    func previous() {
        if position > 5 { seek(0); return }
        previousEpisode()
    }

    /// Previous in the player playlist: the last episode played, then the feed item before it.
    func previousEpisode() {
        if let id = history.popLast(), let item = catalog[id] { play(item, pushHistory: false); return }
        guard let id = story?.id, let index = playlistIndex(of: id), index > 0 else { seek(0); return }
        play(playlist[index - 1], pushHistory: false)
    }

    /// Next in the player playlist: the queued episode if any, otherwise the next feed item.
    func nextEpisode() {
        if !listening.queue.isEmpty { next(); return }
        guard let id = story?.id, let index = playlistIndex(of: id), index + 1 < playlist.count else { return }
        play(playlist[index + 1])
    }
    func persist() {
        flushListeningTime()
        if let data = try? JSONEncoder().encode(listening) { UserDefaults.standard.set(data, forKey: "listeningState") }
        UserDefaults.standard.set(listenedSeconds, forKey: "listenedSeconds")
    }
    private func recordListeningTime(at now: Date) {
        let day = Story.dayFormatter.string(from: now)
        if pendingListenDay != day { flushListeningTime(); pendingListenDay = day }
        pendingListenSeconds += PlaybackTickPolicy.listenedInterval(since: lastTick, now: now)
        lastTick = now
    }
    private func flushListeningTime() {
        guard let day = pendingListenDay, pendingListenSeconds > 0 else { return }
        listenedSeconds[day, default: 0] += pendingListenSeconds
        pendingListenSeconds = 0
    }
    func checkpoint() { if !isPreview && !listening.completed.contains(story?.id ?? "") { listening.checkpoint(position) }; persist() }
    func restore(_ stories: [Story]) {
        for item in stories { catalog[item.id] = item }
        feed = stories.map(\.id)
        if story == nil, let id = listening.currentID, let item = catalog[id] {
            story = item; position = listening.positions[id] ?? 0; duration = Double(item.minutes * 60)
        }
    }
    func enqueue(_ item: Story) { catalog[item.id] = item; listening.enqueue(item.id); persist() }
    func removeQueued(_ id: String) { listening.queue.removeAll { $0 == id }; persist() }
    func moveQueued(_ id: String, by amount: Int) { listening.move(id, by: amount); persist() }
    func clearQueue() { listening.queue = []; persist() }
    func playEdition(_ items: [Story]) {
        guard let first = items.first else { return }
        restore(items); listening.queue = Array(items.dropFirst().map(\.id)); play(first)
    }
    func next() {
        checkpoint()
        while let id = listening.next() {
            if let item = catalog[id] { play(item); return }
        }
        persist()
    }
    private func finished() {
        lastTick = nil; playing = false; updateNowPlaying(); listening.finish(); persist()
        // Pop before play so a completed item's checkpoint cannot be restored.
        while let id = listening.next() {
            if let item = catalog[id] { play(item); return }
        }
        persist()
    }
    func clearListeningData() {
        pause()
        if let observer { player?.removeTimeObserver(observer) }; observer = nil
        if let endObserver { NotificationCenter.default.removeObserver(endObserver) }; endObserver = nil
        player = nil; activeUtterance = nil; speech.stopSpeaking(at: .immediate)
        dialogue = []; dialogueIndex = 0; inDialogue = false
        listening = ListeningState(); listenedSeconds = [:]; story = nil; position = 0; history = []; cancelSleep(); persist()
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }
    /// Re-assert the playback session so audio resumes after calls, routes or backgrounding.
    @discardableResult
    private func activateSession() -> Bool {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, mode: .spokenAudio)
            try session.setActive(true)
            return true
        } catch {
            message = "Audio couldn't start. Please try again."
            playing = false
            Telemetry.audio.error("audio session activation failed: \(String(describing: error), privacy: .public)")
            return false
        }
    }
    /// Device-voice co-hosted playback: speak each turn with its presenter's voice,
    /// advancing on completion. Produced dialogue uses one AVPlayer instead.
    private func startDialogue(_ turns: [DialogueTurn]) {
        dialogue = turns; dialogueIndex = 0; inDialogue = true
        speakDialogueTurn()
    }

    private func speakDialogueTurn() {
        guard inDialogue, dialogue.indices.contains(dialogueIndex) else { return }
        let turn = dialogue[dialogueIndex]
        let utterance = AVSpeechUtterance(string: turn.text)
        utterance.voice = dialogueVoice(for: turn.speaker)
        utterance.pitchMultiplier = dialoguePitch(for: turn.speaker)
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate * rate
        activeUtterance = utterance
        if duration > 0 { position = duration * Double(dialogueIndex) / Double(max(dialogue.count, 1)) }
        speech.speak(utterance)
    }

    private func dialogueVoice(for speaker: String) -> AVSpeechSynthesisVoice? {
        let id = Host.all.first { $0.name == speaker }?.id ?? ""
        let language = ["jax": "en-US", "kai": "en-GB", "benny": "en-AU", "chase": "en-IE",
                        "ines": "en-IE", "dev": "en-IN"][id] ?? "en-US"
        return AVSpeechSynthesisVoice(language: language) ?? AVSpeechSynthesisVoice(language: "en-US")
    }

    private func dialoguePitch(for speaker: String) -> Float {
        let id = Host.all.first { $0.name == speaker }?.id ?? ""
        return ["jax": 1.04, "kai": 0.88, "benny": 1.14, "chase": 0.96, "ines": 1.0, "dev": 1.08][id] ?? 1.0
    }

    func play(_ item: Story, host: Host? = nil, pushHistory: Bool = true) {
        if pushHistory, let current = story, current.id != item.id {
            history.append(current.id)
            if history.count > 25 { history.removeFirst() }
        }
        checkpoint()
        lastTick = nil
        catalog[item.id] = item
        let resumePosition = listening.positions[item.id] ?? 0
        listening.begin(item.id); persist()
        if let observer { player?.removeTimeObserver(observer) }; observer = nil
        if let endObserver { NotificationCenter.default.removeObserver(endObserver) }; endObserver = nil
        player?.pause(); player = nil; activeUtterance = nil; speech.stopSpeaking(at: .immediate)
        dialogue = []; dialogueIndex = 0; inDialogue = false
        story = item; position = item.audioURL == nil ? 0 : resumePosition; duration = Double(item.minutes * 60); message = nil; lastSyncedSecond = -1
        guard activateSession() else { return }
        if item.audioURL == nil, let turns = item.turns, !turns.isEmpty {
            startDialogue(turns)
        } else if let raw = item.audioURL, let url = Self.resolve(raw) {
            let av = AVPlayer(url: url); player = av
            av.audiovisualBackgroundPlaybackPolicy = .continuesIfPossible
            if resumePosition > 0 { av.seek(to: CMTime(seconds: resumePosition, preferredTimescale: 600)) }
            observer = av.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.25, preferredTimescale: 600), queue: .main) { [weak self] time in
                Task { @MainActor in
                    guard let self, self.story?.id == item.id else { return }
                    let position = time.seconds.isFinite ? time.seconds : 0
                    if PlaybackTickPolicy.shouldPublish(current: self.position, next: position) { self.position = position }
                    if self.playing {
                        self.recordListeningTime(at: .now)
                    } else { self.lastTick = nil }
                    if abs(self.position - self.lastCheckpointAt) >= 5 { self.lastCheckpointAt = self.position; self.checkpoint() }
                    if Int(self.position) != self.lastSyncedSecond { self.lastSyncedSecond = Int(self.position); self.updateNowPlaying() }
                    if let seconds = self.player?.currentItem?.duration.seconds, seconds.isFinite, seconds > 0,
                       abs(self.duration - seconds) > 0.05 { self.duration = seconds }
                    if self.player?.currentItem?.status == .failed { self.message = "This audio is unavailable. You can still read the story."; self.playing = false }
                }
            }
            endObserver = NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: av.currentItem, queue: .main) { [weak self] _ in
                Task { @MainActor in guard self?.story?.id == item.id else { return }; self?.finished() }
            }
            av.playImmediately(atRate: rate)
        } else if item.isDemo {
            let utterance = AVSpeechUtterance(string: item.title + ". " + item.body)
            let selected = host ?? item.host
            utterance.voice = AVSpeechSynthesisVoice(language: selected.id == "nova" ? "en-GB" : "en-US")
            utterance.pitchMultiplier = selected.id == "fern" ? 1.12 : selected.id == "atlas" ? 0.9 : 1.0
            utterance.rate = AVSpeechUtteranceDefaultSpeechRate * rate
            activeUtterance = utterance
            speech.speak(utterance)
        } else { message = "Narration is not ready yet. You can still read this story."; playing = false; return }
        playing = true; onStarted?(item)
        updateNowPlaying()
    }
    /// Episode audio is streamed from HTTPS URLs supplied by the feed.
    static func resolve(_ raw: String) -> URL? {
        guard let url = URL(string: raw), url.scheme == "https" else { return nil }
        return url
    }
    func pause() { player?.pause(); speech.pauseSpeaking(at: .immediate); playing = false; lastTick = nil; checkpoint(); updateNowPlaying() }
    func resume() {
        guard story != nil else { return }
        guard activateSession() else { return }
        if let player, !listening.completed.contains(story?.id ?? "") { player.playImmediately(atRate: rate) }
        else if speech.isPaused { speech.continueSpeaking() }
        else if let story { play(story); return }
        playing = true
        updateNowPlaying()
    }
    /// 0 = not started, 1 = finished.
    func progress(of item: Story) -> Double {
        let seconds = item.id == story?.id && !isPreview ? position : (listening.positions[item.id] ?? 0)
        return ListeningMath.progress(position: seconds, duration: max(item.durationSeconds, 1),
                                      completed: listening.completed.contains(item.id))
    }
    func minutesLeft(of item: Story) -> Int { ListeningMath.minutesLeft(progress: progress(of: item), duration: item.durationSeconds) }
    func minutes(on day: Date) -> Int { Int(((listenedSeconds[Story.dayFormatter.string(from: day)] ?? 0) / 60).rounded()) }
    var minutesToday: Int { minutes(on: .now) }
    /// All listening time ever logged on this device.
    var totalMinutes: Int { Int((listenedSeconds.values.reduce(0, +) / 60).rounded()) }
    /// Last seven days, oldest first.
    var week: [(day: Date, minutes: Int)] {
        (0..<7).reversed().compactMap { offset in
            Calendar.current.date(byAdding: .day, value: -offset, to: Calendar.current.startOfDay(for: .now))
        }.map { ($0, minutes(on: $0)) }
    }
    var minutesThisWeek: Int {
        let days = (0..<7).compactMap { Calendar.current.date(byAdding: .day, value: -$0, to: .now) }.map { Story.dayFormatter.string(from: $0) }
        return ListeningMath.minutes(seconds: days.reduce(0) { $0 + (listenedSeconds[$1] ?? 0) })
    }
    /// Consecutive days (ending today or yesterday) with at least a minute of listening.
    var streakDays: Int {
        ListeningMath.streak(seconds: listenedSeconds, today: .now) { Story.dayFormatter.string(from: $0) }
    }
    func toggle() { playing ? pause() : resume() }
    func seek(_ value: Double) {
        guard player != nil, value.isFinite else { return }
        position = min(max(0, value), duration)
        player?.seek(to: CMTime(seconds: position, preferredTimescale: 600))
        updateNowPlaying()
    }
    func cycleRate() { rate = rate == 1 ? 1.25 : rate == 1.25 ? 1.5 : 1; if playing { player?.rate = rate }; if isPreview { message = "Preview speed applies the next time you start a story." }; updateNowPlaying() }
    func sleep(minutes: Int) {
        sleepTask?.cancel(); sleepUntil = Date.now.addingTimeInterval(Double(minutes * 60))
        sleepTask = Task { try? await Task.sleep(for: .seconds(minutes * 60)); guard !Task.isCancelled else { return }; pause(); sleepUntil = nil }
        message = "Playback will pause in \(minutes) minutes."
    }
    func cancelSleep() { sleepTask?.cancel(); sleepTask = nil; sleepUntil = nil; message = nil }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in
            guard self.activeUtterance === utterance else { return }
            self.activeUtterance = nil
            if self.inDialogue {
                self.dialogueIndex += 1
                if self.dialogueIndex < self.dialogue.count {
                    self.speakDialogueTurn()
                } else {
                    self.inDialogue = false
                    self.finished()
                }
            } else {
                self.finished()
            }
        }
    }
}
