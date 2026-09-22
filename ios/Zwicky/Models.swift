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
        Host(id: "jax", name: "Jax Moreno", niche: "Astrophysics", personality: "Loud questions, quick jokes, real science.", symbol: "star", hue: 0.72),
        Host(id: "kai", name: "Kai Nakamura", niche: "Astrophysics", personality: "The quiet one who does the maths.", symbol: "function", hue: 0.20),
        Host(id: "benny", name: "Benny Osei", niche: "Astrophysics", personality: "Allergic to a boring comparison.", symbol: "flame", hue: 0.88),
        Host(id: "chase", name: "Chase Delacroix", niche: "Astrophysics", personality: "The sceptic with the best punchlines.", symbol: "star.fill", hue: 0.96)
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
             about: "Oceans, weather, geology and climate, with the patience these slow systems deserve. New episodes are on the way; a sample is available now.",
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
    /// Spoken conversation when an episode is co-hosted. Optional so older
    /// single-host JSON without the key keeps decoding.
    let turns: [DialogueTurn]?
    /// Every host heard on a multi-host episode; the primary stays `hostID`.
    let hostIDs: [String]?
    var host: Host { Host.all.first { $0.id == hostID } ?? Show.forHost(hostID)?.host ?? Host.all[0] }
    var show: Show { Show.forHost(hostID) ?? Show.all[0] }
    var durationSeconds: Double { Episodes.duration(for: id) ?? Double(minutes * 60) }
    var publishedDate: Date? { published.flatMap { Story.dayFormatter.date(from: $0) } }
    /// "Sep 17", or "Sample" for device-voice demos without a date.
    var dateText: String { publishedDate?.formatted(.dateTime.month(.abbreviated).day()) ?? (isDemo ? "Sample" : "") }
    static let dayFormatter: DateFormatter = { let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_US_POSIX"); return f }()
    /// A device-voice demo for the four-host comedy show, so the co-hosted
    /// format is playable before any produced narration exists.
    static let starBrosTurns: [DialogueTurn] = [
        DialogueTurn(speaker: "Jax Moreno", text: "Okay, serious question. Why is the night sky dark? There are billions of stars. Why isn't the whole sky just glowing?"),
        DialogueTurn(speaker: "Kai Nakamura", text: "That's Olbers' paradox. It's a good question, which is annoying."),
        DialogueTurn(speaker: "Benny Osei", text: "It's the one where the universe answers a question about the sky with a fact about time."),
        DialogueTurn(speaker: "Chase Delacroix", text: "The old answer goes like this. If the universe were infinite, unchanging and infinitely old, every direction you looked would eventually hit a star, and the whole sky would be as bright as the surface of the Sun."),
        DialogueTurn(speaker: "Jax Moreno", text: "Which it is not. I have seen the sky. It is very dark. I was there."),
        DialogueTurn(speaker: "Kai Nakamura", text: "Two things are wrong with that setup. The universe is not infinitely old, and it is not standing still."),
        DialogueTurn(speaker: "Chase Delacroix", text: "It is about thirteen point eight billion years old, and light has a speed. So there is a horizon. We only see sources whose light has had time to reach us."),
        DialogueTurn(speaker: "Benny Osei", text: "The sky is dark because the universe has a birthday."),
        DialogueTurn(speaker: "Kai Nakamura", text: "And because it is expanding. Space itself stretches the light on its way here, so distant light arrives redshifted, its energy spread thinner."),
        DialogueTurn(speaker: "Jax Moreno", text: "So the far stuff doesn't just get quieter. It gets redder and dimmer. That is somehow worse, and cooler."),
        DialogueTurn(speaker: "Chase Delacroix", text: "Both. The finite age sets the horizon, and expansion dims whatever crosses it."),
        DialogueTurn(speaker: "Benny Osei", text: "A nice thought: darkness isn't the absence of stars. It's a message about how the whole thing began."),
        DialogueTurn(speaker: "Kai Nakamura", text: "Careful. It's evidence, not a message."),
        DialogueTurn(speaker: "Jax Moreno", text: "Kai. Let him have one."),
        DialogueTurn(speaker: "Benny Osei", text: "I'll take one."),
        DialogueTurn(speaker: "Chase Delacroix", text: "The clean version: a bright sky is what you would get from an infinite, eternal, static cosmos. We don't live in one, and the dark sky is one of the ways we can tell."),
        DialogueTurn(speaker: "Jax Moreno", text: "So every clear night is a measurement. That's genuinely beautiful, and I'm not even being ironic."),
        DialogueTurn(speaker: "Kai Nakamura", text: "You're a little bit being ironic."),
        DialogueTurn(speaker: "Jax Moreno", text: "A little bit."),
        DialogueTurn(speaker: "Benny Osei", text: "Look up tonight. The dark parts are data."),
        DialogueTurn(speaker: "Chase Delacroix", text: "And the bright parts are the exceptions we can actually see."),
        DialogueTurn(speaker: "Kai Nakamura", text: "That's the whole thing. Check the assumptions."),
        DialogueTurn(speaker: "Jax Moreno", text: "Okay, that was good. I'm Jax Moreno, and the universe is rude and I love it."),
        DialogueTurn(speaker: "Benny Osei", text: "I'm Benny Osei. Stay curious about the dark."),
        DialogueTurn(speaker: "Chase Delacroix", text: "I'm Chase Delacroix. Look it up, it's called Olbers' paradox."),
    ]
    static let starBrosSample: Story = Story(
        id: "demo-star-bros-dark-sky",
        title: "Why the night sky is dark",
        dek: "Four friends, one very old question, and a universe that will not sit still.",
        topic: "ASTROPHYSICS", hostID: "jax", minutes: 3,
        body: Story.starBrosTurns.map(\.text).joined(separator: " "),
        caveat: "An original device-voice sample with four synthetic presenters. Written as a demonstration; the source is general background, not a new study, and neither the script nor the voices have had editorial approval.",
        sources: [Source(title: "NASA Science: Universe", url: "https://science.nasa.gov/universe/",
                         attribution: "NASA Science", license: "Public domain (NASA)")],
        audioURL: nil, isDemo: true,
        turns: Story.starBrosTurns, hostIDs: ["jax", "kai", "benny", "chase"])
    /// Voiced preview episodes bundled with the app, plus a device-voice demo for hosts without one yet.
    /// Every episode ships with the app; see backend/bundle_episodes.py.
    static let demos: [Story] = Episodes.bundled.map(\.story) + [starBrosSample]
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
    /// Episode ids from Episodes/index.json, falling back to the four shipped demos.
    static let ids: [String] = {
        if let url = Bundle.main.url(forResource: "index", withExtension: "json"),
           let data = try? Data(contentsOf: url),
           let names = try? JSONDecoder().decode([String].self, from: data), !names.isEmpty {
            return names
        }
        return ["mira", "clara", "elias", "theo"]
    }()
    static let bundled: [BundledEpisode] = ids.compactMap { name in
        guard let url = Bundle.main.url(forResource: name, withExtension: "json"), let data = try? Data(contentsOf: url) else { return nil }
        return try? JSONDecoder().decode(BundledEpisode.self, from: data)
    }
    /// Streamed episodes' transcript + envelope, fetched on demand from `Story.detailURL`.
    static var remote: [String: BundledEpisode] = [:]
    static func episode(for storyID: String) -> BundledEpisode? {
        bundled.first { $0.story.id == storyID } ?? remote[storyID]
    }
    /// Fetch and cache a streamed episode's sidecar so read-along works off the feed.
    static func load(_ story: Story) async {
        if episode(for: story.id) != nil { return }
        guard let raw = story.detailURL, let url = URL(string: raw), url.scheme == "https" else { return }
        guard let (data, response) = try? await URLSession.shared.data(from: url),
              (response as? HTTPURLResponse)?.statusCode == 200,
              let decoded = try? JSONDecoder().decode(BundledEpisode.self, from: data) else { return }
        remote[story.id] = decoded
    }
    static func transcript(for storyID: String) -> [TranscriptParagraph]? { episode(for: storyID)?.transcript }
    static func duration(for storyID: String) -> Double? { episode(for: storyID)?.duration }
    static func levels(for storyID: String) -> (frames: [[Double]], hop: Double)? {
        guard let episode = episode(for: storyID), !episode.levels.isEmpty else { return nil }
        return (episode.levels, episode.levelHop)
    }
}

@MainActor final class Library: ObservableObject {
    @Published private(set) var stories: [Story]
    @Published var saved: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "saved") ?? [])
    @Published var history: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "history") ?? [])
    @Published var error: String?
    @Published var loading = false
    @Published var following: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "following") ?? Show.all.map(\.id))
    /// True when a configured feed failed to refresh and the cached copy is shown.
    @Published var isOffline = false
    @Published private(set) var feedCachedAt: Date?
    @AppStorage("host") var hostID = "nova"
    @AppStorage("dailyGoalMinutes") var dailyGoalMinutes = 10
    /// A local, anonymous profile. No account exists yet; these fields are the
    /// upgradeable identity described in docs/SOCIAL-PLAN.md.
    @AppStorage("profileName") var profileName = ""
    @AppStorage("profileSymbol") var profileSymbol = "person.fill"
    @AppStorage("profileHue") var profileHue = 0.66
    @AppStorage("joinedStamp") private var joinedStamp = ""
    var displayName: String {
        let trimmed = profileName.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "Listener" : trimmed
    }
    var initials: String {
        displayName.split(separator: " ").prefix(2).compactMap { $0.first.map(String.init) }.joined().uppercased()
    }
    var joined: Date? { Story.dayFormatter.date(from: joinedStamp) }
    func ensureJoined() { if joinedStamp.isEmpty { joinedStamp = Story.dayFormatter.string(from: .now) } }
    private var feed: [Story] = []
    private var pinned: [Story] = []

    init() {
        pinned = StoryCache.loadPinned()
        if let cached = StoryCache.loadFeed() {
            feed = cached.stories
            feedCachedAt = cached.cachedAt
        } else {
            feed = Story.demos
        }
        stories = []
        rebuild()
    }

    /// Feed order first, then pinned stories no longer in the feed.
    private func rebuild() {
        var seen = Set<String>()
        stories = (feed + pinned).filter { seen.insert($0.id).inserted }
    }

    /// Keep full records for items the listener saved, heard, queued or is playing.
    func pin(_ items: [Story]) {
        guard !items.isEmpty else { return }
        for item in items {
            if let index = pinned.firstIndex(where: { $0.id == item.id }) { pinned[index] = item }
            else { pinned.append(item) }
        }
        StoryCache.savePinned(pinned)
        rebuild()
    }
    func isFollowing(_ show: Show) -> Bool { following.contains(show.id) }
    func toggleFollow(_ show: Show) {
        if following.contains(show.id) { following.remove(show.id) } else { following.insert(show.id) }
        UserDefaults.standard.set(Array(following), forKey: "following")
    }
    func setFollowing(_ ids: Set<String>) { following = ids; UserDefaults.standard.set(Array(ids), forKey: "following") }
    /// Newest first; undated samples last.
    var latest: [Story] { stories.sorted { ($0.published ?? "") > ($1.published ?? "") } }
    func episodes(of show: Show) -> [Story] { latest.filter { show.hostIDs.contains($0.hostID) } }
    @AppStorage("feedURL") var feedURL = ""
    func toggle(_ story: Story) {
        if saved.contains(story.id) { saved.remove(story.id) } else { saved.insert(story.id) }
        UserDefaults.standard.set(Array(saved), forKey: "saved")
        pin([story])
    }
    func heard(_ story: Story) {
        history.insert(story.id)
        UserDefaults.standard.set(Array(history), forKey: "history")
        pin([story])
    }
    func refresh() async {
        guard !feedURL.isEmpty else { return }
        guard let url = URL(string: feedURL), url.scheme == "https" else { error = "Use an HTTPS feed URL."; return }
        loading = true; defer { loading = false }
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
            feed = try JSONDecoder().decode([Story].self, from: data)
            feedCachedAt = .now
            StoryCache.saveFeed(feed)
            isOffline = false
            error = nil
            rebuild()
        } catch {
            if feedCachedAt != nil {
                isOffline = true
                self.error = nil
            } else {
                self.error = "Couldn't refresh your stories. Your current collection is still available."
            }
        }
    }
}
