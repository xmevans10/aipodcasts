import Foundation

/// Last-good feed and current-feed listener state, persisted to Application Support.
///
/// The feed cache lets a relaunch show stories when the network is unavailable.
/// Pins are retained only while their stories remain in that feed. Audio itself
/// is not downloaded here; remote audio needs a network.
enum StoryCache {
    struct Feed: Codable {
        let schemaVersion: Int
        let stories: [Story]
        let cachedAt: Date
    }
    struct Pinned: Codable {
        let schemaVersion: Int
        let stories: [Story]
    }
    static let schemaVersion = 1

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
        guard let data = try? JSONEncoder().encode(
            Feed(schemaVersion: schemaVersion, stories: stories, cachedAt: .now)) else { return }
        try? data.write(to: feedFile, options: .atomic)
    }

    static func decodeFeed(_ data: Data) -> Feed? {
        guard let feed = try? JSONDecoder().decode(Feed.self, from: data),
              feed.schemaVersion == schemaVersion else { return nil }
        return feed
    }

    static func loadFeed() -> Feed? {
        guard let data = try? Data(contentsOf: feedFile) else { return nil }
        return decodeFeed(data)
    }

    static func savePinned(_ stories: [Story]) {
        guard let data = try? JSONEncoder().encode(
            Pinned(schemaVersion: schemaVersion, stories: stories)) else { return }
        try? data.write(to: pinnedFile, options: .atomic)
    }

    static func decodePinned(_ data: Data) -> [Story]? {
        guard let pinned = try? JSONDecoder().decode(Pinned.self, from: data),
              pinned.schemaVersion == schemaVersion else { return nil }
        return pinned.stories
    }

    static func loadPinned() -> [Story] {
        guard let data = try? Data(contentsOf: pinnedFile) else { return [] }
        return decodePinned(data) ?? []
    }
}
