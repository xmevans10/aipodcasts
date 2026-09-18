import Foundation

/// Last-good feed and pinned stories, persisted to Application Support.
///
/// The feed cache lets a relaunch show stories when the network is unavailable.
/// Pinned stories (saved, heard, queued or current) keep their full body, sources
/// and audio reference even after a feed rotates them out. Audio itself is not
/// downloaded here; `bundle:` audio plays offline, remote audio still needs a network.
enum StoryCache {
    struct Feed: Codable {
        let stories: [Story]
        let cachedAt: Date
    }

    private static let folder: URL = {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSTemporaryDirectory())
        let directory = base.appendingPathComponent("SoundScience", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory
    }()

    private static var feedFile: URL { folder.appendingPathComponent("feed.json") }
    private static var pinnedFile: URL { folder.appendingPathComponent("pinned.json") }

    static func saveFeed(_ stories: [Story]) {
        guard let data = try? JSONEncoder().encode(Feed(stories: stories, cachedAt: .now)) else { return }
        try? data.write(to: feedFile, options: .atomic)
    }

    static func loadFeed() -> Feed? {
        guard let data = try? Data(contentsOf: feedFile),
              let feed = try? JSONDecoder().decode(Feed.self, from: data) else { return nil }
        return feed
    }

    static func savePinned(_ stories: [Story]) {
        guard let data = try? JSONEncoder().encode(stories) else { return }
        try? data.write(to: pinnedFile, options: .atomic)
    }

    static func loadPinned() -> [Story] {
        guard let data = try? Data(contentsOf: pinnedFile),
              let stories = try? JSONDecoder().decode([Story].self, from: data) else { return [] }
        return stories
    }
}
