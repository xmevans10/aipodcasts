import AVFoundation
import MediaPlayer
import SwiftUI

@MainActor final class AudioPlayer: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    @Published var story: Story?
    @Published var playing = false
    @Published var position = 0.0
    @Published var duration = 1.0
    @Published var rate: Float = 1
    @Published var message: String?
    @Published private(set) var listening = ListeningState()
    @Published var sleepUntil: Date?
    var onStarted: ((Story) -> Void)?
    private var catalog: [String: Story] = [:]
    var queuedStories: [Story] { listening.queue.compactMap { catalog[$0] } }
    private var activeUtterance: AVSpeechUtterance?
    private let speech = AVSpeechSynthesizer()
    private var player: AVPlayer?
    private var observer: Any?
    private var endObserver: NSObjectProtocol?
    private var sleepTask: Task<Void, Never>?
    private var lastCheckpointAt = 0.0
    private var lastTick: Date?
    /// Seconds of real audio listened, keyed by local day ("yyyy-MM-dd").
    @Published private(set) var listenedSeconds: [String: Double] = UserDefaults.standard.dictionary(forKey: "listenedSeconds") as? [String: Double] ?? [:]
    var isPreview: Bool { story?.audioURL == nil }
    var hasLoadedAudio: Bool { player != nil }
    override init() {
        super.init(); speech.delegate = self
        if let data = UserDefaults.standard.data(forKey: "listeningState"), let stored = try? JSONDecoder().decode(ListeningState.self, from: data) { listening = stored }
        MPRemoteCommandCenter.shared().playCommand.addTarget { [weak self] _ in Task { @MainActor in self?.resume() }; return .success }
        MPRemoteCommandCenter.shared().pauseCommand.addTarget { [weak self] _ in Task { @MainActor in self?.pause() }; return .success }
    }
    func persist() {
        if let data = try? JSONEncoder().encode(listening) { UserDefaults.standard.set(data, forKey: "listeningState") }
        UserDefaults.standard.set(listenedSeconds, forKey: "listenedSeconds")
    }
    func checkpoint() { if !isPreview && !listening.completed.contains(story?.id ?? "") { listening.checkpoint(position) }; persist() }
    func restore(_ stories: [Story]) {
        for item in stories { catalog[item.id] = item }
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
        playing = false; listening.finish(); persist()
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
        listening = ListeningState(); listenedSeconds = [:]; story = nil; position = 0; cancelSleep(); persist()
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }
    func play(_ item: Story, host: Host? = nil) {
        checkpoint()
        catalog[item.id] = item
        let resumePosition = listening.positions[item.id] ?? 0
        listening.begin(item.id); persist()
        if let observer { player?.removeTimeObserver(observer) }; observer = nil
        if let endObserver { NotificationCenter.default.removeObserver(endObserver) }; endObserver = nil
        player?.pause(); player = nil; activeUtterance = nil; speech.stopSpeaking(at: .immediate)
        story = item; position = item.audioURL == nil ? 0 : resumePosition; duration = Double(item.minutes * 60); message = nil
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch { message = "Audio couldn't start. Please try again."; playing = false; return }
        if let raw = item.audioURL, let url = Self.resolve(raw) {
            let av = AVPlayer(url: url); player = av
            if resumePosition > 0 { av.seek(to: CMTime(seconds: resumePosition, preferredTimescale: 600)) }
            observer = av.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.1, preferredTimescale: 600), queue: .main) { [weak self] time in
                Task { @MainActor in
                    guard let self, self.story?.id == item.id else { return }
                    self.position = time.seconds.isFinite ? time.seconds : 0
                    if self.playing {
                        let now = Date.now
                        if let last = self.lastTick { self.listenedSeconds[Story.dayFormatter.string(from: now), default: 0] += min(now.timeIntervalSince(last), 0.5) }
                        self.lastTick = now
                    } else { self.lastTick = nil }
                    if abs(self.position - self.lastCheckpointAt) >= 5 { self.lastCheckpointAt = self.position; self.checkpoint() }
                    if let seconds = self.player?.currentItem?.duration.seconds, seconds.isFinite, seconds > 0 { self.duration = seconds }
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
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [MPMediaItemPropertyTitle: item.title, MPMediaItemPropertyArtist: "Sound Science · \(item.host.name)"]
    }
    /// Remote audio must be HTTPS; `bundle:name.ext` plays a file shipped with the app.
    static func resolve(_ raw: String) -> URL? {
        if raw.hasPrefix("bundle:") {
            let file = String(raw.dropFirst("bundle:".count)) as NSString
            return Bundle.main.url(forResource: file.deletingPathExtension, withExtension: file.pathExtension)
        }
        guard let url = URL(string: raw), url.scheme == "https" else { return nil }
        return url
    }
    func pause() { player?.pause(); speech.pauseSpeaking(at: .immediate); playing = false; checkpoint() }
    func resume() {
        guard story != nil else { return }
        if let player, !listening.completed.contains(story?.id ?? "") { player.playImmediately(atRate: rate) }
        else if speech.isPaused { speech.continueSpeaking() }
        else if let story { play(story); return }
        playing = true
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
        guard player != nil else { return }
        position = min(max(0, value), duration)
        player?.seek(to: CMTime(seconds: position, preferredTimescale: 600))
    }
    func cycleRate() { rate = rate == 1 ? 1.25 : rate == 1.25 ? 1.5 : 1; if playing { player?.rate = rate }; if isPreview { message = "Preview speed applies the next time you start a story." } }
    func sleep(minutes: Int) {
        sleepTask?.cancel(); sleepUntil = Date.now.addingTimeInterval(Double(minutes * 60))
        sleepTask = Task { try? await Task.sleep(for: .seconds(minutes * 60)); guard !Task.isCancelled else { return }; pause(); sleepUntil = nil }
        message = "Playback will pause in \(minutes) minutes."
    }
    func cancelSleep() { sleepTask?.cancel(); sleepTask = nil; sleepUntil = nil; message = nil }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in guard self.activeUtterance === utterance else { return }; self.activeUtterance = nil; self.finished() }
    }
}
