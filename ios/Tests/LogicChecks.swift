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

private func testPlaybackTickPolicy() {
    check(!PlaybackTickPolicy.shouldPublish(current: 12, next: 12.03), "tiny clock changes do not refresh the UI")
    check(PlaybackTickPolicy.shouldPublish(current: 12, next: 12.25), "visible clock changes refresh the UI")
    check(PlaybackTickPolicy.shouldPublish(current: 42, next: 12), "seeking backwards refreshes the UI")
    check(!PlaybackTickPolicy.shouldPublish(current: 12, next: .nan), "invalid player time is ignored")
    check(PlaybackTickPolicy.shouldPublish(current: .nan, next: 12), "a valid tick repairs invalid clock state")

    let start = Date(timeIntervalSince1970: 100)
    checkEqual(PlaybackTickPolicy.listenedInterval(since: nil, now: start), 0, "the first tick adds no listening time")
    checkEqual(PlaybackTickPolicy.listenedInterval(since: start, now: start.addingTimeInterval(0.25)), 0.25,
               "normal playback counts elapsed time")
    checkEqual(PlaybackTickPolicy.listenedInterval(since: start, now: start.addingTimeInterval(3)), 0.5,
               "a stalled callback cannot overcount listening")
    checkEqual(PlaybackTickPolicy.listenedInterval(since: start, now: start.addingTimeInterval(-1)), 0,
               "clock changes cannot subtract listening time")
}

// MARK: - shows and hosts

private func testShowsAndHosts() {
    checkEqual(Show.all.count, 16, "sixteen shows")
    checkEqual(Set(Show.all.map(\.id)).count, 16, "show ids are unique")
    checkEqual(Set(Show.all.map(\.title)).count, 16, "show titles are unique")
    checkEqual(Set(Host.all.map(\.id)).count, Host.all.count, "host ids are unique")
    for show in Show.all {
        check(!show.hostIDs.isEmpty, "\(show.title) names at least one host")
        check(show.hostIDs.allSatisfy { id in Host.all.contains { $0.id == id } },
              "\(show.title) hostIDs resolve to real hosts")
        check(show.hostIDs.contains(show.host.id), "\(show.title) exposes a primary host")
        check(!show.tagline.isEmpty && !show.about.isEmpty, "\(show.title) has copy for its page")
        check(Show.forHost(show.hostIDs[0])?.id == show.id, "\(show.title) resolves from its primary host")
    }
    for host in Host.all {
        let shows = Show.all.filter { $0.hostIDs.contains(host.id) }
        checkEqual(shows.count, 1, "\(host.name) maps to exactly one show")
        checkEqual(host.show.id, shows.first?.id, "\(host.name) resolves its show")
    }
}

// MARK: - episode cache migration

@MainActor private func testEpisodeCacheMigration() {
    let oldFeed = #"{"stories":[],"cachedAt":0}"#.data(using: .utf8)!
    let officialURL = Library.defaultFeedURL
    check(StoryCache.decodeFeed(oldFeed, for: officialURL) == nil, "unversioned episode feed caches are discarded")
    let current = StoryCache.Feed(schemaVersion: StoryCache.schemaVersion, sourceURL: officialURL,
                                  stories: [], cachedAt: .now)
    let currentData = try! JSONEncoder().encode(current)
    checkEqual(StoryCache.decodeFeed(currentData, for: officialURL)?.schemaVersion,
               StoryCache.schemaVersion, "official feed caches remain readable")
    check(StoryCache.decodeFeed(currentData, for: "https://other.example/feed.json") == nil,
          "a different feed cannot reuse the official catalog cache")
}

// MARK: - story helpers

private func testStoryHelpers() {
    let story = Story(id: "x", title: "T", dek: "D", topic: "SPACE", hostID: "nova", minutes: 3,
                      body: "b", caveat: "c", sources: [], audioURL: nil, isDemo: false, published: "2026-09-17",
                      turns: nil, hostIDs: nil)
    checkEqual(story.publishedDate.map { Story.dayFormatter.string(from: $0) }, "2026-09-17", "published dates parse")
    check(story.dateText.contains("17"), "a published episode shows its date")
    checkEqual(story.durationSeconds, 180, "an unbundled episode falls back to its minute count")
    check(story.sharingURL == nil, "an episode without a link has no share action")
    var shareable = story
    shareable.shareURL = "http://example.org/episode"
    check(shareable.sharingURL == nil, "insecure episode share URLs are ignored")
    shareable.shareURL = "https://example.org/episode"
    checkEqual(shareable.sharingURL?.absoluteString, "https://example.org/episode",
               "published listening pages are shareable")
    let undated = Story(id: "y", title: "T", dek: "D", topic: "EARTH", hostID: "atlas", minutes: 1,
                        body: "b", caveat: "c", sources: [], audioURL: nil, isDemo: true,
                        turns: nil, hostIDs: nil)
    checkEqual(undated.dateText, "Sample", "an undated demo is labelled a sample")
}

// MARK: - dialogue decoding

private func testDialogueFields() {
    let legacy = """
    {"id":"l","title":"T","dek":"D","topic":"SPACE","hostID":"nova","minutes":3,"body":"b","caveat":"c","sources":[],"isDemo":false}
    """.data(using: .utf8)!
    guard let old = try? JSONDecoder().decode(Story.self, from: legacy) else {
        failures.append("a story without dialogue keys no longer decodes"); checks += 1; return
    }
    checkEqual(old.turns, nil, "legacy stories have no dialogue turns")
    checkEqual(old.hostIDs, nil, "legacy stories keep just the primary host")
    checkEqual(old.show.id, "the-long-view", "legacy stories still resolve their show")

    let dialogue = """
    {"id":"d","title":"T","dek":"D","topic":"METHODS","hostID":"ines","minutes":4,"body":"b","caveat":"c","sources":[],"isDemo":false,"hostIDs":["ines","dev"],"turns":[{"speaker":"Ines Marlowe","text":"Hi."},{"speaker":"Dev Raman","text":"Hello."}]}
    """.data(using: .utf8)!
    guard let decoded = try? JSONDecoder().decode(Story.self, from: dialogue) else {
        failures.append("a dialogue story does not decode"); checks += 1; return
    }
    checkEqual(decoded.turns?.count, 2, "dialogue turns decode in order")
    checkEqual(decoded.turns?.first?.speaker, "Ines Marlowe", "a turn keeps its speaker")
    checkEqual(decoded.hostIDs, ["ines", "dev"], "co-hosts decode")
    checkEqual(decoded.show.id, "ground-truth", "a co-hosted story resolves its show")
    let paragraphs = """
    [{"words":[{"text":"Hello.","start":0}]},{"speaker":"Dev Raman","hostID":"dev","words":[{"text":"Hi.","start":1.18}]}]
    """.data(using: .utf8)!
    let timed = try! JSONDecoder().decode([TranscriptParagraph].self, from: paragraphs)
    checkEqual(timed[0].speaker, nil, "legacy solo paragraphs decode without speakers")
    checkEqual(timed[1].speaker, "Dev Raman", "read-along preserves speaker attribution")
    checkEqual(timed[1].hostID, "dev", "read-along preserves stable host id")
    checkEqual(timed[1].words[0].start, 1.18, "read-along preserves absolute turn offset")
    checkEqual(try! JSONDecoder().decode([TranscriptParagraph].self, from: JSONEncoder().encode(timed)),
               timed, "speaker paragraphs round-trip without loss")
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
        testListeningState()
        testListeningMath()
        testPlaybackTickPolicy()
        testShowsAndHosts()
        testStoryHelpers()
        testDialogueFields()
        MainActor.assumeIsolated {
            testEpisodeCacheMigration()
            testCoverLayout()
        }

        if failures.isEmpty {
            print("✓ \(checks) checks passed")
        } else {
            print("✗ \(failures.count) of \(checks) checks failed:")
            for failure in failures { print("   - \(failure)") }
            exit(1)
        }
    }
}
