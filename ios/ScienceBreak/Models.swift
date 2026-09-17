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
        Host(id: "atlas", name: "Theo Mercer", niche: "Human discovery", personality: "The human story behind the science.", symbol: "fingerprint", hue: 0.47)
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
    var host: Host { Host.all.first { $0.id == hostID } ?? Host.all[0] }
    static let demos: [Story] = [
        Story(id: "cosmic", title: "The universe has a way of keeping receipts.", dek: "How ancient light lets us look back in time.", topic: "SPACE", hostID: "nova", minutes: 2, body: "Look up at the night sky and you are looking into the past. Light travels at a finite speed, so even sunlight takes about eight minutes to reach Earth.\n\nFor distant galaxies, that journey can take billions of years. A telescope is therefore a kind of time machine: it catches light that began travelling long before our planet looked the way it does today.\n\nAs the universe expands, travelling light stretches toward longer wavelengths. Astronomers call this redshift. Infrared instruments can detect some of this stretched light, helping researchers investigate early galaxies.\n\nThe beautiful part is also the difficult part. We see a snapshot from long ago, and scientists must work carefully to infer the story around it. A brighter dot does not automatically settle how a galaxy formed.\n\nNext time you look up, remember: the sky is a collection of arrivals. Each point of light has been on a journey.", caveat: "Evergreen demonstration script, not a report of a new discovery. Distances and galaxy ages require models and uncertainty estimates.", sources: [Source(title: "NASA: Webb science", url: "https://science.nasa.gov/mission/webb/", attribution: "Science Break original educational demo; background reading: NASA", license: "Original demo")], audioURL: nil, isDemo: true),
        Story(id: "forest", title: "A forest is more than its trees.", dek: "Meet the quiet chemistry happening under your feet.", topic: "NATURE", hostID: "fern", minutes: 1, body: "A forest does not stop where the soil begins. Roots, fungi, bacteria and tiny animals all help shape what grows above ground.\n\nSome fungi form partnerships with plant roots. Plants supply carbon compounds made through photosynthesis, while fungi can help them access nutrients. These relationships vary across species and environments.\n\nYou may have heard forests described as a wood wide web. It is a memorable metaphor, but it can encourage claims that go beyond the evidence. Networks do not necessarily mean that trees are deliberately talking or helping one another.\n\nThe real science is interesting enough: a complex, changing set of relationships that researchers are still working to understand.", caveat: "A metaphor is not evidence of intention. This is an evergreen educational demo, not a new study.", sources: [Source(title: "PLOS Biology", url: "https://journals.plos.org/plosbiology/", attribution: "Science Break original educational demo; journal provided for further discovery", license: "Original demo")], audioURL: nil, isDemo: true),
        Story(id: "brain", title: "Your brain is always editing the story.", dek: "Why remembering is an act of reconstruction.", topic: "MIND", hostID: "ada", minutes: 1, body: "Memory can feel like pressing play on a recording. In reality, remembering involves reconstruction.\n\nOur brains use traces of previous experiences alongside context and expectations. This helps us make sense of the world, but also means that a vivid memory is not necessarily a perfect record.\n\nResearchers study these processes using carefully designed tasks. A result in one task does not explain every kind of memory, and individuals differ.\n\nThe useful takeaway is modest: confidence and accuracy are different things. Staying curious about our own recollections is part of staying curious about the world.", caveat: "General educational information. Not clinical advice or a report of a specific new experiment.", sources: [Source(title: "PLOS Biology", url: "https://journals.plos.org/plosbiology/", attribution: "Science Break original educational demo; journal provided for further discovery", license: "Original demo")], audioURL: nil, isDemo: true),
        Story(id: "ocean", title: "The ocean has a very long memory.", dek: "The enormous role of water in a warming world.", topic: "EARTH", hostID: "atlas", minutes: 1, body: "Water takes a lot of energy to warm up. Across the planet, that makes the ocean an enormous reservoir of heat.\n\nCurrents move heat through the ocean, and exchanges with the atmosphere influence climate. What happens at the surface is only part of the picture.\n\nScientists combine instruments, satellite observations and models to understand these changes. Each method has limitations, particularly when measuring the deep ocean.\n\nThinking about the ocean changes how we think about climate: some responses unfold over very long periods, well beyond a single season or year.", caveat: "Evergreen demo. No new measurements or study results are asserted here.", sources: [Source(title: "NASA Earth science", url: "https://science.nasa.gov/earth/", attribution: "Science Break original educational demo; background reading: NASA", license: "Original demo")], audioURL: nil, isDemo: true)
    ]
}

@MainActor final class Library: ObservableObject {
    @Published var stories = Story.demos
    @Published var saved: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "saved") ?? [])
    @Published var history: Set<String> = Set(UserDefaults.standard.stringArray(forKey: "history") ?? [])
    @Published var error: String?
    @Published var loading = false
    @AppStorage("host") var hostID = "nova"
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
