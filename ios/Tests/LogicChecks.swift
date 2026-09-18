import Foundation
import SwiftUI

/// Headless unit tests for the app's pure logic: queue state, listening maths and the
/// bundled episode data. Runs without a simulator — see scripts/run-ios-tests.sh.
/// UI behaviour is not covered here; that still needs a device or simulator.

private var failures: [String] = []
private var checks = 0

private func check(_ condition: Bool, _ what: String, file: StaticString = #file, line: UInt = #line) {
    checks += 1
    if !condition { failures.append("\(what)  (line \(line))") }
}

private func checkEqual<T: Equatable>(_ actual: T, _ expected: T, _ what: String, line: UInt = #line) {
    checks += 1
    if actual != expected { failures.append("\(what): expected \(expected), got \(actual)  (line \(line))") }
}

// MARK: - queue and resume state

private func testListeningState() {
    var state = ListeningState()
    state.begin("a")
    state.enqueue("a"); state.enqueue("b"); state.enqueue("b"); state.enqueue("c")
    checkEqual(state.queue, ["b", "c"], "queue excludes the current item and duplicates")

    state.move("b", by: -1)
    checkEqual(state.queue, ["b", "c"], "moving past the start is ignored")
    state.move("c", by: -1)
    checkEqual(state.queue, ["c", "b"], "an item moves up")

    state.checkpoint(42); state.checkpoint(.nan); state.checkpoint(-1)
    checkEqual(state.positions["a"], 42, "invalid progress cannot corrupt resume")

    let restored = try! JSONDecoder().decode(ListeningState.self, from: JSONEncoder().encode(state))
    check(restored.queue == state.queue && restored.positions == state.positions && restored.currentID == "a",
          "state survives a round trip through storage")

    state.finish()
    check(state.completed.contains("a"), "finishing marks the episode played")
    checkEqual(state.positions["a"], nil, "finishing clears the resume position")
    checkEqual(state.next(), "c", "next pops the front of the queue")

    state.begin("a")
    check(!state.completed.contains("a"), "replaying clears the played mark")
}

// MARK: - listening maths

private func testListeningMath() {
    checkEqual(ListeningMath.progress(position: 0, duration: 180, completed: false), 0, "unstarted reads zero")
    checkEqual(ListeningMath.progress(position: 90, duration: 180, completed: false), 0.5, "half way reads a half")
    checkEqual(ListeningMath.progress(position: 400, duration: 180, completed: false), 0.99,
               "an overrun never reaches 1 unless finished")
    checkEqual(ListeningMath.progress(position: 5, duration: 180, completed: true), 1, "finished reads 1")
    checkEqual(ListeningMath.progress(position: .nan, duration: 180, completed: false), 0, "NaN is not progress")
    checkEqual(ListeningMath.progress(position: 10, duration: 0, completed: false), 0, "a zero duration is not progress")

    checkEqual(ListeningMath.minutesLeft(progress: 0, duration: 180), 3, "a fresh three-minute episode has 3 min left")
    checkEqual(ListeningMath.minutesLeft(progress: 0.99, duration: 180), 1, "the last moments still read as a minute")

    checkEqual(ListeningMath.minutes(seconds: 0), 0, "no listening is zero minutes")
    checkEqual(ListeningMath.minutes(seconds: 89), 1, "89 seconds rounds to a minute")

    // streaks
    let calendar = Calendar(identifier: .gregorian)
    let formatter = DateFormatter()
    formatter.dateFormat = "yyyy-MM-dd"
    formatter.locale = Locale(identifier: "en_US_POSIX")
    formatter.calendar = calendar
    let key: (Date) -> String = { formatter.string(from: $0) }
    let today = calendar.startOfDay(for: Date(timeIntervalSince1970: 1_789_000_000))
    func day(_ offset: Int) -> String { key(calendar.date(byAdding: .day, value: offset, to: today)!) }

    checkEqual(ListeningMath.streak(seconds: [:], today: today, calendar: calendar, key: key), 0, "no listening, no streak")
    checkEqual(ListeningMath.streak(seconds: [day(0): 120, day(-1): 300, day(-2): 90],
                                    today: today, calendar: calendar, key: key), 3, "three consecutive days count")
    checkEqual(ListeningMath.streak(seconds: [day(0): 120, day(-1): 30, day(-2): 300],
                                    today: today, calendar: calendar, key: key), 1,
               "a day under a minute breaks the streak")
    checkEqual(ListeningMath.streak(seconds: [day(-1): 120, day(-2): 120],
                                    today: today, calendar: calendar, key: key), 2,
               "a streak survives until today is missed entirely")
    checkEqual(ListeningMath.streak(seconds: [day(-2): 600], today: today, calendar: calendar, key: key), 0,
               "a gap of two days ends the streak")
}

// MARK: - shows and hosts

private func testShowsAndHosts() {
    checkEqual(Show.all.count, 4, "four shows")
    checkEqual(Set(Show.all.map(\.id)).count, 4, "show ids are unique")
    checkEqual(Set(Show.all.map(\.title)).count, 4, "show titles are unique")
    for show in Show.all {
        checkEqual(show.host.id, show.id, "\(show.title) resolves its own host")
        check(!show.tagline.isEmpty && !show.about.isEmpty, "\(show.title) has copy for its page")
    }
    for host in Host.all {
        check(Show.all.contains { $0.id == host.id }, "\(host.name) fronts a show")
    }
}

// MARK: - bundled episodes

private func testEpisodes(directory: URL) {
    let names = ["mira", "clara", "elias", "theo"]
    for name in names {
        let url = directory.appendingPathComponent("\(name).json")
        guard let data = try? Data(contentsOf: url),
              let episode = try? JSONDecoder().decode(BundledEpisode.self, from: data) else {
            failures.append("\(name).json does not decode as an episode"); checks += 1; continue
        }
        let story = episode.story
        checkEqual(story.audioURL, "bundle:\(name).m4a", "\(name) points at its bundled audio")
        check(FileManager.default.fileExists(atPath: directory.appendingPathComponent("\(name).m4a").path),
              "\(name).m4a ships beside its metadata")
        check(Show.all.contains { $0.id == story.hostID }, "\(name) belongs to a real show")
        check(!story.sources.isEmpty, "\(name) cites at least one source")
        check(story.sources.allSatisfy { $0.url.hasPrefix("https://") }, "\(name) source links are HTTPS")
        check(!story.caveat.isEmpty, "\(name) carries its limitations note")
        check(episode.duration > 30, "\(name) is a real episode length")

        // transcript: every word timed, in order, inside the episode
        let words = episode.transcript.flatMap(\.words)
        check(!words.isEmpty, "\(name) has a timed transcript")
        check(zip(words, words.dropFirst()).allSatisfy { $0.start <= $1.start }, "\(name) word timings never go backwards")
        check(words.first!.start >= 0 && words.last!.start <= episode.duration,
              "\(name) word timings sit inside the episode")
        let transcriptWords = episode.transcript.flatMap { $0.words.map(\.text) }.joined(separator: " ")
        let bodyWords = story.body.split(whereSeparator: \.isWhitespace).joined(separator: " ")
        checkEqual(transcriptWords, bodyWords, "\(name) transcript matches the episode body word for word")

        // audio envelope: five bands per frame, 0...1, roughly one frame per hop
        check(!episode.levels.isEmpty, "\(name) has an audio envelope")
        check(episode.levels.allSatisfy { $0.count == 5 }, "\(name) envelope has five bands per frame")
        check(episode.levels.allSatisfy { $0.allSatisfy { (0...1).contains($0) } }, "\(name) envelope stays in 0...1")
        let expectedFrames = episode.duration / episode.levelHop
        check(abs(Double(episode.levels.count) - expectedFrames) < 5,
              "\(name) envelope covers the episode (\(episode.levels.count) frames vs \(Int(expectedFrames)))")
        check(episode.levels.contains { $0.contains { $0 > 0.5 } }, "\(name) envelope actually peaks")
    }
}

// MARK: - story helpers

private func testStoryHelpers() {
    let story = Story(id: "x", title: "T", dek: "D", topic: "SPACE", hostID: "nova", minutes: 3,
                      body: "b", caveat: "c", sources: [], audioURL: nil, isDemo: false, published: "2026-09-17")
    checkEqual(story.publishedDate.map { Story.dayFormatter.string(from: $0) }, "2026-09-17", "published dates parse")
    check(story.dateText.contains("17"), "a published episode shows its date")
    checkEqual(story.durationSeconds, 180, "an unbundled episode falls back to its minute count")
    let undated = Story(id: "y", title: "T", dek: "D", topic: "EARTH", hostID: "atlas", minutes: 1,
                        body: "b", caveat: "c", sources: [], audioURL: nil, isDemo: true)
    checkEqual(undated.dateText, "Sample", "an undated demo is labelled a sample")
}

// MARK: - cover layout
//
// A cover that sizes itself to its decorative sheen stops being square and drags the
// row's text across it. These render the real view and measure what comes out.

@MainActor private func testCoverLayout() {
    for width in [42.0, 60.0, 84.0, 160.0, 300.0] {
        let renderer = ImageRenderer(content: ShowCover(show: Show.all[0]).frame(width: width))
        renderer.scale = 1
        guard let image = renderer.cgImage else {
            failures.append("cover at \(Int(width))pt did not render"); checks += 1; continue
        }
        checkEqual(image.width, Int(width), "cover at \(Int(width))pt is the requested width")
        checkEqual(image.height, Int(width), "cover at \(Int(width))pt is square")
    }
}

@main struct LogicChecks {
    static func main() {
        let episodes = URL(fileURLWithPath: CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "Zwicky/Episodes")
        testListeningState()
        testListeningMath()
        testShowsAndHosts()
        testStoryHelpers()
        testEpisodes(directory: episodes)
        MainActor.assumeIsolated { testCoverLayout() }

        if failures.isEmpty {
            print("✓ \(checks) checks passed")
        } else {
            print("✗ \(failures.count) of \(checks) checks failed:")
            for failure in failures { print("   - \(failure)") }
            exit(1)
        }
    }
}
