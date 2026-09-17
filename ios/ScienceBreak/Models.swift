import SwiftUI

struct Host: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let niche: String
    let personality: String
    let symbol: String
    let hue: Double
    var color: Color { Color(hue: hue, saturation: 0.28, brightness: 0.88) }
    static let all = [
        Host(id: "nova", name: "Mira Vale", niche: "Space & physics", personality: "Big questions. A little cosmic perspective.", symbol: "sparkles", hue: 0.66),
        Host(id: "fern", name: "Clara Rowan", niche: "Our living planet", personality: "Wild connections, told with warmth.", symbol: "leaf", hue: 0.27),
        Host(id: "ada", name: "Elias Reed", niche: "Minds & machines", personality: "Curious, clear-eyed, delightfully nerdy.", symbol: "waveform.path", hue: 0.06),
        Host(id: "atlas", name: "Theo Mercer", niche: "Earth & climate", personality: "The planet beneath the headlines, told patiently.", symbol: "touchid", hue: 0.47)
    ]
}
/// Each host fronts their own show; the app is the platform that carries all of them.
struct Show: Identifiable, Hashable {
    let id: String  // matches Host.id
    let title: String
    let category: String
    let tagline: String
    let about: String
    let symbol: String
    let light: Color
    let dark: Color
    var host: Host { Host.all.first { $0.id == id } ?? Host.all[0] }
    static let all = [
        Show(id: "nova", title: "The Long View", category: "Space & Physics", tagline: "Space, time and the stuff in between.",
             about: "New findings from telescopes, orbiters and physics labs, explained calmly and without the hype. Each episode follows how we know, not just what was found.",
             symbol: "moon.stars", light: Color(hex: 0x7D8BE0), dark: Color(hex: 0x232B5E)),
        Show(id: "fern", title: "Wild Company", category: "Nature & Wildlife", tagline: "The living world, up close.",
             about: "Animals, plants and ecosystems doing surprising things. Stories come from field observations and peer-reviewed studies, with their limits kept in view.",
             symbol: "leaf", light: Color(hex: 0x8CC084), dark: Color(hex: 0x1F4A36)),
        Show(id: "ada", title: "Signal & Noise", category: "Brain & Technology", tagline: "How minds and machines make sense of things.",
             about: "Neuroscience, perception and computing, taken apart one mechanism at a time. Expect careful distinctions between what was measured and what was modelled.",
             symbol: "waveform.path.ecg", light: Color(hex: 0xE6936A), dark: Color(hex: 0x6E2A1C)),
        Show(id: "atlas", title: "Common Ground", category: "Earth & Climate", tagline: "The planet beneath the headlines.",
             about: "Oceans, weather, geology and climate, with the patience these slow systems deserve. New episodes are on the way; a sample is available now.",
             symbol: "globe.americas", light: Color(hex: 0x62B6B7), dark: Color(hex: 0x0E4553)),
    ]
}
struct Source: Codable, Hashable {
    let title: String
    let url: String
    let attribution: String
    let license: String
}
struct Story: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let dek: String
    let topic: String
    let hostID: String
    let minutes: Int
    let body: String
    let caveat: String
    let sources: [Source]
    let audioURL: String?
    let isDemo: Bool
    var published: String? = nil
    var host: Host { Host.all.first { $0.id == hostID } ?? Host.all[0] }
    var show: Show { Show.all.first { $0.id == hostID } ?? Show.all[0] }
    var durationSeconds: Double { Episodes.duration(for: id) ?? Double(minutes * 60) }
    var publishedDate: Date? { published.flatMap { Story.dayFormatter.date(from: $0) } }
    /// "Sep 17", or "Sample" for device-voice demos without a date.
    var dateText: String { publishedDate?.formatted(.dateTime.month(.abbreviated).day()) ?? (isDemo ? "Sample" : "") }
    static let dayFormatter: DateFormatter = { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX"); return f }()
    /// Voiced preview episodes bundled with the app, plus a device-voice demo for hosts without one yet.
    static let demos: [Story] = Episodes.bundled.map(\.story) + [
        Story(id: "ocean", title: "The ocean has a very long memory.", dek: "The enormous role of water in a warming world.", topic: "EARTH", hostID: "atlas", minutes: 1, body: "Water takes a lot of energy to warm up. Across the planet, that makes the ocean an enormous reservoir of heat.\n\nCurrents move heat through the ocean, and exchanges with the atmosphere influence climate. What happens at the surface is only part of the picture.\n\nScientists combine instruments, satellite observations and models to understand these changes. Each method has limitations, particularly when measuring the deep ocean.\n\nThinking about the ocean changes how we think about climate: some responses unfold over very long periods, well beyond a single season or year.", caveat: "Evergreen demo. No new measurements or study results are asserted here.", sources: [Source(title: "NASA Earth science", url: "https://science.nasa.gov/earth/", attribution: "Sound Science original educational demo; background reading: NASA", license: "Original demo")], audioURL: nil, isDemo: true)
    ]
}

struct TranscriptWord: Codable, Hashable { let text: String; let start: Double }
struct TranscriptParagraph: Codable, Hashable { let words: [TranscriptWord] }
struct BundledEpisode: Codable {
    let story: Story
    let duration: Double
    let transcript: [TranscriptParagraph]
    /// Five-band audio levels (0...1) every `levelHop` seconds, from backend/envelope.py.
    var levels: [[Double]] = []
    var levelHop: Double = 0.1
}
/// Episodes shipped in the app bundle (Episodes/*.json + .m4a), generated by backend/bundle_episodes.py.
enum Episodes {
    static let bundled: [BundledEpisode] = ["mira", "clara", "elias"].compactMap { name in
        guard let url = Bundle.main.url(forResource: name, withExtension: "json"), let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(BundledEpisode.self, from: data)
    }
    static func transcript(for storyID: String) -> [TranscriptParagraph]? { bundled.first { $0.story.id == storyID }?.transcript }
    static func duration(for storyID: String) -> Double? { bundled.first { $0.story.id == storyID }?.duration }
    static func levels(for storyID: String) -> (frames: [[Double]], hop: Double)? {
        guard let episode = bundled.first(where: { $0.story.id == storyID }), !episode.levels.isEmpty else { return nil }
        return (episode.levels, episode.levelHop)
    }
}

@MainActor final class Library: ObservableObject {
    @Published var stories = Story.demos
    @Published var saved: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "saved") ?? [])
    @Published var history: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "history") ?? [])
    @Published var error: String?
    @Published var loading = false
    @Published var following: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "following") ?? Show.all.map(\.id))
    @AppStorage("host") var hostID = "nova"
    @AppStorage("dailyGoalMinutes") var dailyGoalMinutes = 10
    func isFollowing(_ show: Show) -> Bool { following.contains(show.id) }
    func toggleFollow(_ show: Show) {
        if following.contains(show.id) { following.remove(show.id) } else { following.insert(show.id) }
        UserDefaults.standard.set(Array(following), forKey: "following")
    }
    func setFollowing(_ ids: Set<String>) { following = ids; UserDefaults.standard.set(Array(ids), forKey: "following") }
    /// Newest first; undated samples last.
    var latest: [Story] { stories.sorted { ($0.published ?? "") > ($1.published ?? "") } }
    func episodes(of show: Show) -> [Story] { latest.filter { $0.hostID == show.id } }
    @AppStorage("feedURL") var feedURL = ""
    func toggle(_ story: Story) {
        if saved.contains(story.id) { saved.remove(story.id) } else { saved.insert(story.id) }
        UserDefaults.standard.set(Array(saved), forKey: "saved")
    }
    func heard(_ story: Story) {
        history.insert(story.id)
        UserDefaults.standard.set(Array(history), forKey: "history")
    }
    func refresh() async {
        guard !feedURL.isEmpty else { return }
        guard let url = URL(string: feedURL), url.scheme == "https" else { error = "Use an HTTPS feed URL."; return }
        loading = true; defer { loading = false }
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
            stories = try JSONDecoder().decode([Story].self, from: data)
            error = nil
        } catch { self.error = "Couldn't refresh your stories. Your current collection is still available." }
    }
}
