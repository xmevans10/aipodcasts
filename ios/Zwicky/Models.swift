import SwiftUI

struct Host: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let niche: String
    let personality: String
    let symbol: String
    let hue: Double
    var color: Color { Color(hue: hue, saturation: 0.28, brightness: 0.88) }
    /// The single show this host fronts.
    var show: Show { Show.forHost(id) ?? Show.all[0] }
    var showID: String { show.id }
    static let all = [
        Host(id: "nova", name: "Mira Vale", niche: "Space & physics", personality: "Big questions. A little cosmic perspective.", symbol: "sparkles", hue: 0.66),
        Host(id: "fern", name: "Clara Rowan", niche: "Our living planet", personality: "Wild connections, told with warmth.", symbol: "leaf", hue: 0.27),
        Host(id: "ada", name: "Elias Reed", niche: "Minds & machines", personality: "Curious, clear-eyed, delightfully nerdy.", symbol: "waveform.path", hue: 0.06),
        Host(id: "atlas", name: "Theo Mercer", niche: "Earth & climate", personality: "The planet beneath the headlines, told patiently.", symbol: "touchid", hue: 0.47),
        Host(id: "spinner", name: "Dr. Priya Nandakumar", niche: "Spiders & silk", personality: "Reads a web like a blueprint, one thread at a time.", symbol: "point.3.connected.trianglepath.dotted", hue: 0.76),
        Host(id: "yusuf", name: "Dr. Yusuf Adeyemi", niche: "Stars & astrochemistry", personality: "The atoms in you were forged in stars, and he can show you how.", symbol: "atom", hue: 0.10),
        Host(id: "noor", name: "Dr. Noor Haddad", niche: "AI & machine learning", personality: "Clear about what a model learned, and what it didn't.", symbol: "cpu", hue: 0.58),
        Host(id: "marek", name: "Marek Novak", niche: "3D printing & materials", personality: "Prints the part, then tests the part.", symbol: "cube.transparent", hue: 0.03),
        Host(id: "tomas", name: "Dr. Tomas Iversen", niche: "Sports science", personality: "Marginal gains, measured honestly.", symbol: "figure.run", hue: 0.30),
        Host(id: "lena", name: "Dr. Lena Petrova", niche: "Sleep & circadian", personality: "Takes rest seriously, one rhythm at a time.", symbol: "moon.zzz", hue: 0.62),
        Host(id: "rosa", name: "Dr. Rosa Ibarra", niche: "Fungi & networks", personality: "Follows the network underground.", symbol: "network", hue: 0.82),
        Host(id: "amara", name: "Dr. Amara Okafor", niche: "Bees & pollinators", personality: "Small pollinators, large consequences.", symbol: "hexagon", hue: 0.14),
        Host(id: "kenji", name: "Dr. Kenji Watanabe", niche: "Deep sea", personality: "Pressure, darkness and patience.", symbol: "water.waves", hue: 0.52),
        Host(id: "freya", name: "Dr. Freya Lindqvist", niche: "Ancient DNA", personality: "Deep time, read from a fragment of bone.", symbol: "fossil.shell", hue: 0.36),
        Host(id: "ines", name: "Ines Marlowe", niche: "Methods & evidence", personality: "Precise, gently sceptical, always checking the method.", symbol: "checkmark.seal", hue: 0.00),
        Host(id: "dev", name: "Dev Raman", niche: "Methods & evidence", personality: "Warm translator from a result to what it changes.", symbol: "text.bubble", hue: 0.41),
        Host(id: "jax", name: "Jackson \"Jax\" Ruiz", niche: "Astrophysics", personality: "Loud questions, quick jokes, real science.", symbol: "star", hue: 0.72),
        Host(id: "kai", name: "Kai Nakamura", niche: "Astrophysics", personality: "The quiet one who does the maths.", symbol: "function", hue: 0.20),
        Host(id: "benny", name: "Benny Ortiz", niche: "Astrophysics", personality: "Allergic to a boring comparison.", symbol: "flame", hue: 0.88),
        Host(id: "chase", name: "Chase Whitaker", niche: "Astrophysics", personality: "The sceptic with the best punchlines.", symbol: "star.fill", hue: 0.96)
    ]
}
/// A show may be fronted by one host or a small cast; `id` is a stable slug.
struct Show: Identifiable, Hashable {
    let id: String  // stable slug, not a host id
    let title: String
    let category: String
    let tagline: String
    let about: String
    let symbol: String
    let light: Color
    let mid: Color
    let dark: Color
    let hostIDs: [String]
    /// The first host listed is the show's primary voice.
    var host: Host { Host.all.first { hostIDs.contains($0.id) } ?? Host.all[0] }
    /// The first show a host appears on, if any.
    static func forHost(_ id: String) -> Show? { all.first { $0.hostIDs.contains(id) } }
    static let all = [
        Show(id: "the-long-view", title: "The Long View", category: "Space & Physics", tagline: "Space, time and the stuff in between.",
             about: "New findings from telescopes, orbiters and physics labs, explained calmly and without the hype. Each episode follows how we know, not just what was found.",
             symbol: "moon.stars", light: Color(hex: 0x8F7CFF), mid: Color(hex: 0x4B49C8), dark: Color(hex: 0x151A52), hostIDs: ["nova"]),
        Show(id: "wild-company", title: "Wild Company", category: "Nature & Wildlife", tagline: "The living world, up close.",
             about: "Animals, plants and ecosystems doing surprising things. Stories come from field observations and peer-reviewed studies, with their limits kept in view.",
             symbol: "leaf", light: Color(hex: 0xA8E063), mid: Color(hex: 0x2FA46B), dark: Color(hex: 0x0C3B2E), hostIDs: ["fern"]),
        Show(id: "signal-and-noise", title: "Signal & Noise", category: "Brain & Technology", tagline: "How minds and machines make sense of things.",
             about: "Neuroscience, perception and computing, taken apart one mechanism at a time. Expect careful distinctions between what was measured and what was modelled.",
             symbol: "waveform.path.ecg", light: Color(hex: 0xFF9A5A), mid: Color(hex: 0xE4572E), dark: Color(hex: 0x5B1A12), hostIDs: ["ada"]),
        Show(id: "common-ground", title: "Common Ground", category: "Earth & Climate", tagline: "The planet beneath the headlines.",
             about: "Oceans, weather, geology and climate, with the patience these slow systems deserve.",
             symbol: "globe.americas", light: Color(hex: 0x59D8D0), mid: Color(hex: 0x139BB0), dark: Color(hex: 0x07374A), hostIDs: ["atlas"]),
        Show(id: "webwork", title: "Webwork", category: "Spiders & Arachnids", tagline: "Eight legs, one extraordinary material.",
             about: "Spiders, their webs and the silk they spin, from garden orb-weavers to the physics of a thread thinner than a hair. Every claim is traced back to the study that made it.",
             symbol: "circle.hexagonpath", light: Color(hex: 0xA98CFF), mid: Color(hex: 0x6A3FC0), dark: Color(hex: 0x241246), hostIDs: ["spinner"]),
        Show(id: "star-stuff", title: "Star Stuff", category: "Stars & Astrochemistry", tagline: "The chemistry that built the elements.",
             about: "Stars forge the atoms we are made of, and astrochemists read that history in spectra and dust. New episodes follow the molecules, not the mystique.",
             symbol: "atom", light: Color(hex: 0xFF9FD8), mid: Color(hex: 0xC93F9B), dark: Color(hex: 0x3E0A32), hostIDs: ["yusuf"]),
        Show(id: "gradient", title: "Gradient", category: "AI & Machine Learning", tagline: "What machine learning actually learns.",
             about: "Neural networks, training data and the difference between a benchmark and the world. Careful explanations of what models do, and where their confidence stops.",
             symbol: "cpu", light: Color(hex: 0x6FC8E8), mid: Color(hex: 0x1F6FA8), dark: Color(hex: 0x0A2440), hostIDs: ["noor"]),
        Show(id: "layer-by-layer", title: "Layer by Layer", category: "3D Printing & Materials", tagline: "Building things one layer at a time.",
             about: "3D printing, new materials and the engineering between a digital file and a physical part. Prints are tested, not just demonstrated.",
             symbol: "cube.transparent", light: Color(hex: 0xE8B48A), mid: Color(hex: 0x9A5426), dark: Color(hex: 0x35190A), hostIDs: ["marek"]),
        Show(id: "marginal-gains", title: "Marginal Gains", category: "Sports Science", tagline: "Small edges, honestly measured.",
             about: "Sports science, training and recovery, where a one-percent change is the whole game. Effect sizes and study limits are kept in plain sight.",
             symbol: "figure.run", light: Color(hex: 0xBEE05A), mid: Color(hex: 0x5A9A22), dark: Color(hex: 0x1E3608), hostIDs: ["tomas"]),
        Show(id: "slow-wave", title: "Slow Wave", category: "Sleep & Circadian", tagline: "The science of sleep and rhythm.",
             about: "Sleep, circadian clocks and what rest does to body and mind. Evidence first; no miracle routines.",
             symbol: "moon.zzz", light: Color(hex: 0x9AA6FF), mid: Color(hex: 0x4453B0), dark: Color(hex: 0x11143A), hostIDs: ["lena"]),
        Show(id: "mycelium", title: "Mycelium", category: "Fungi & Networks", tagline: "The network beneath the forest floor.",
             about: "Fungi, mycelium and the partnerships they run underground. A quiet world of connections, explained from the field and the lab.",
             symbol: "network", light: Color(hex: 0xD99BCB), mid: Color(hex: 0x8F4580), dark: Color(hex: 0x33122B), hostIDs: ["rosa"]),
        Show(id: "hive-mind", title: "Hive Mind", category: "Bees & Pollinators", tagline: "Small pollinators, planetary stakes.",
             about: "Bees, wasps and the pollination webs they hold together. Colony life and its pressures, told with the evidence attached.",
             symbol: "hexagon", light: Color(hex: 0xFFC24D), mid: Color(hex: 0xCC7400), dark: Color(hex: 0x401F00), hostIDs: ["amara"]),
        Show(id: "the-deep", title: "The Deep", category: "Deep Sea", tagline: "Life and pressure at the bottom.",
             about: "The deep sea: dark, cold and stranger than fiction. Explorations and the instruments that make them possible.",
             symbol: "water.waves", light: Color(hex: 0x5FB8D8), mid: Color(hex: 0x19648F), dark: Color(hex: 0x051A33), hostIDs: ["kenji"]),
        Show(id: "old-bones", title: "Old Bones", category: "Ancient DNA", tagline: "Deep time, written in DNA.",
             about: "Ancient DNA and what bones and sediments reveal about the deep past. Reconstructions are careful, and their uncertainties named.",
             symbol: "fossil.shell", light: Color(hex: 0xDCC79A), mid: Color(hex: 0xA07C40), dark: Color(hex: 0x33250F), hostIDs: ["freya"]),
        Show(id: "ground-truth", title: "Ground Truth", category: "Methods & Evidence", tagline: "Two hosts, one question: how do we know?",
             about: "Ines Marlowe and Dev Raman take a single result and pull it apart: how it was measured, what it means and where it stops holding. A co-hosted show about evidence.",
             symbol: "chart.xyaxis.line", light: Color(hex: 0x8FA6BC), mid: Color(hex: 0x3F5C76), dark: Color(hex: 0x101B26), hostIDs: ["ines", "dev"]),
        Show(id: "star-bros", title: "Star Bros", category: "Astrophysics", tagline: "Four friends, one enormous universe.",
             about: "Jax, Kai, Benny and Chase argue, joke and explain their way through astrophysics. Warm, silly and genuinely rigorous, with the science always landing.",
             symbol: "star", light: Color(hex: 0xFF8F6B), mid: Color(hex: 0xB23A6E), dark: Color(hex: 0x3A0C29), hostIDs: ["jax", "kai", "benny", "chase"])
    ]
}
struct Source: Codable, Hashable {
    let title: String
    let url: String
    let attribution: String
    let license: String
}
/// One spoken turn in a co-hosted episode.
struct DialogueTurn: Codable, Hashable { let speaker: String; let text: String }
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
    /// Absolute URL of the streamed episode's transcript + envelope sidecar, if any.
    var detailURL: String? = nil
    /// Public listening page. Older feed entries can still share their audio URL.
    var shareURL: String? = nil
    /// Spoken conversation when an episode is co-hosted. Optional so older
    /// single-host JSON without the key keeps decoding.
    let turns: [DialogueTurn]?
    /// Every host heard on a multi-host episode; the primary stays `hostID`.
    let hostIDs: [String]?
    var host: Host { Host.all.first { $0.id == hostID } ?? Show.forHost(hostID)?.host ?? Host.all[0] }
    var show: Show { Show.forHost(hostID) ?? Show.all[0] }
    var durationSeconds: Double { Episodes.duration(for: id) ?? Double(minutes * 60) }
    var sharingURL: URL? {
        for raw in [shareURL, audioURL].compactMap({ $0 }) {
            if let url = URL(string: raw), url.scheme == "https" { return url }
        }
        return nil
    }
    var publishedDate: Date? { published.flatMap { Story.dayFormatter.date(from: $0) } }
    /// "Sep 17", or "Sample" for device-voice demos without a date.
    var dateText: String { publishedDate?.formatted(.dateTime.month(.abbreviated).day()) ?? (isDemo ? "Sample" : "") }
    /// Published within the last seven days, so it can carry a NEW badge.
    var isFresh: Bool {
        guard let date = publishedDate else { return false }
        return date >= Calendar.current.date(byAdding: .day, value: -7, to: .now) ?? .distantPast
    }
    static let dayFormatter: DateFormatter = { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX"); return f }()
}

struct TranscriptWord: Codable, Hashable {
    let text: String
    let start: Double
    /// When the word finishes in the audio, from the waveform aligner. Optional so
    /// sidecars rendered before alignment (start-only) still decode.
    var end: Double? = nil
}
struct TranscriptParagraph: Codable, Hashable {
    let words: [TranscriptWord]
    var speaker: String? = nil
    var hostID: String? = nil
}
struct BundledEpisode: Codable {
    let story: Story
    let duration: Double
    let transcript: [TranscriptParagraph]
    /// Five-band audio levels (0...1) every `levelHop` seconds, from backend/envelope.py.
    var levels: [[Double]] = []
    var levelHop: Double = 0.1
}
/// Metadata for streamed episodes. Episode catalogs and audio arrive only through the feed.
enum Episodes {
    /// Streamed episodes' transcript + envelope, fetched on demand from `Story.detailURL`.
    static var remote: [String: BundledEpisode] = [:]
    static func episode(for storyID: String) -> BundledEpisode? { remote[storyID] }
    /// Fetch and cache a streamed episode's sidecar so read-along works off the feed.
    static func load(_ story: Story) async {
        if episode(for: story.id) != nil { return }
        guard let raw = story.detailURL, let url = URL(string: raw), url.scheme == "https" else { return }
        await Telemetry.measure("episodes.sidecar") {
            guard let (data, response) = try? await URLSession.shared.data(from: url),
                  (response as? HTTPURLResponse)?.statusCode == 200,
                  let decoded = try? JSONDecoder().decode(BundledEpisode.self, from: data) else {
                Telemetry.feed.error("sidecar \(story.id, privacy: .public) failed")
                return
            }
            remote[story.id] = decoded
            Telemetry.feed.debug("sidecar \(story.id, privacy: .public) \(data.count, privacy: .public) bytes")
        }
    }
    static func transcript(for storyID: String) -> [TranscriptParagraph]? { episode(for: storyID)?.transcript }
    static func duration(for storyID: String) -> Double? { episode(for: storyID)?.duration }
    static func levels(for storyID: String) -> (frames: [[Double]], hop: Double)? {
        guard let episode = episode(for: storyID), !episode.levels.isEmpty else { return nil }
        return (episode.levels, episode.levelHop)
    }
}

@MainActor final class Library: ObservableObject {
    /// Published feed of streamed episodes (R2).
    static let defaultFeedURL = "https://pub-e19f5de621fd4b4ea01c0465d0251407.r2.dev/v1/feed.json"
    @Published private(set) var stories: [Story]
    @Published var saved: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "saved") ?? [])
    @Published var history: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "history") ?? [])
    @Published var error: String?
    @Published var loading = false
    @Published var following: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "following") ?? Show.all.map(\.id))
    /// True when a configured feed failed to refresh and the cached copy is shown.
    @Published var isOffline = false
    @Published private(set) var feedCachedAt: Date?
    /// Newest published date the listener has already been told about, so we only
    /// announce genuinely new episodes (stored across launches).
    @AppStorage("lastSeenPublished") var lastSeenPublished = ""
    /// Set once the new-episodes sheet has been shown this launch.
    @Published var announcedNew = false
    @AppStorage("host") var hostID = "nova"
    @AppStorage("dailyGoalMinutes") var dailyGoalMinutes = 10
    /// A local, anonymous profile. No account exists yet; these fields are the
    /// upgradeable identity described in docs/SOCIAL-PLAN.md.
    @Published var profileName = UserDefaults.standard.string(forKey: "profileName") ?? "" {
        didSet { UserDefaults.standard.set(profileName, forKey: "profileName") }
    }
    @Published var profileBio = UserDefaults.standard.string(forKey: "profileBio") ?? "" {
        didSet { UserDefaults.standard.set(profileBio, forKey: "profileBio") }
    }
    @Published var favoriteShowID = UserDefaults.standard.string(forKey: "favoriteShowID") ?? "" {
        didSet { UserDefaults.standard.set(favoriteShowID, forKey: "favoriteShowID") }
    }
    @Published var profileSymbol = UserDefaults.standard.string(forKey: "profileSymbol") ?? "person.fill" {
        didSet { UserDefaults.standard.set(profileSymbol, forKey: "profileSymbol") }
    }
    @Published var profileHue = (UserDefaults.standard.object(forKey: "profileHue") as? Double) ?? 0.66 {
        didSet { UserDefaults.standard.set(profileHue, forKey: "profileHue") }
    }
    @AppStorage("joinedStamp") private var joinedStamp = ""
    var displayName: String {
        let trimmed = profileName.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "Listener" : trimmed
    }
    var initials: String {
        displayName.split(separator: " ").prefix(2).compactMap { $0.first.map(String.init) }.joined().uppercased()
    }
    var joined: Date? { Story.dayFormatter.date(from: joinedStamp) }
    var favoriteShow: Show? { Show.all.first { $0.id == favoriteShowID } }
    func ensureJoined() { if joinedStamp.isEmpty { joinedStamp = Story.dayFormatter.string(from: .now) } }
    private var feed: [Story] = []
    init() {
        let start = Telemetry.now()
        stories = []
        StoryCache.removeLegacyPins()
        UserDefaults.standard.removeObject(forKey: "feedURL")
        if let cached = StoryCache.loadFeed(for: feedURL) {
            feed = cached.stories
            feedCachedAt = cached.cachedAt
        }
        rebuild()
        Telemetry.app.info("Library init \(Telemetry.ms(since: start), format: .fixed(precision: 1)) ms; \(self.feed.count, privacy: .public) cached episodes")
    }

    private func rebuild() {
        stories = feed
    }

    func isFollowing(_ show: Show) -> Bool { following.contains(show.id) }
    func toggleFollow(_ show: Show) {
        if following.contains(show.id) { following.remove(show.id) } else { following.insert(show.id) }
        UserDefaults.standard.set(Array(following), forKey: "following")
    }
    func setFollowing(_ ids: Set<String>) { following = ids; UserDefaults.standard.set(Array(ids), forKey: "following") }
    /// Newest first.
    var latest: [Story] { stories.sorted { ($0.published ?? "") > ($1.published ?? "") } }
    func episodes(of show: Show) -> [Story] { latest.filter { show.hostIDs.contains($0.hostID) } }
    var feedURL: String { Library.defaultFeedURL }
    func toggle(_ story: Story) {
        if saved.contains(story.id) { saved.remove(story.id) } else { saved.insert(story.id) }
        UserDefaults.standard.set(Array(saved), forKey: "saved")
    }
    func heard(_ story: Story) {
        history.insert(story.id)
        UserDefaults.standard.set(Array(history), forKey: "history")
    }
    /// Episodes published after the last acknowledged marker, newest first.
    var newEpisodes: [Story] {
        guard !lastSeenPublished.isEmpty else { return [] }
        return stories.filter { ($0.published ?? "") > lastSeenPublished }
            .sorted { ($0.published ?? "") > ($1.published ?? "") }
    }
    var unseenNewCount: Int { newEpisodes.count }
    var shouldAnnounceNew: Bool { !announcedNew && !newEpisodes.isEmpty }
    /// Acknowledge the new episodes: advance the marker and stop announcing this launch.
    func markNewSeen() {
        lastSeenPublished = stories.compactMap { $0.published }.max() ?? lastSeenPublished
        announcedNew = true
    }
    func refresh() async {
        guard !loading else { return }
        guard !feedURL.isEmpty else { return }
        guard let url = URL(string: feedURL), url.scheme == "https" else { error = "Use an HTTPS feed URL."; return }
        loading = true; defer { loading = false }
        let start = Telemetry.now()
        do {
            let request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData)
            let (data, response) = try await URLSession.shared.data(for: request)
            let status = (response as? HTTPURLResponse)?.statusCode ?? -1
            let fetchedAt = Telemetry.ms(since: start)
            guard status == 200 else { throw URLError(.badServerResponse) }
            feed = try JSONDecoder().decode([Story].self, from: data)
            let decodedAt = Telemetry.ms(since: start)
            feedCachedAt = .now
            StoryCache.saveFeed(feed, sourceURL: feedURL)
            isOffline = false
            error = nil
            rebuild()
            // First run: remember where "new" starts so we don't announce the back catalogue.
            if lastSeenPublished.isEmpty {
                lastSeenPublished = feed.compactMap { $0.published }.max() ?? ""
            }
            Telemetry.feed.info("refresh ok: \(self.feed.count, privacy: .public) episodes, \(data.count, privacy: .public) bytes; fetch \(fetchedAt, format: .fixed(precision: 1)) ms, decode \(decodedAt, format: .fixed(precision: 1)) ms")
        } catch {
            let elapsed = Telemetry.ms(since: start)
            if feedCachedAt != nil {
                isOffline = true
                self.error = nil
                Telemetry.feed.error("refresh failed after \(elapsed, format: .fixed(precision: 1)) ms (status/error), showing cached feed: \(String(describing: error), privacy: .public)")
            } else {
                self.error = "Couldn't load episodes. Check your connection and retry."
                Telemetry.feed.error("refresh failed after \(elapsed, format: .fixed(precision: 1)) ms with no cache: \(String(describing: error), privacy: .public)")
            }
        }
    }
}
