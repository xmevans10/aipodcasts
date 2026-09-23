import Foundation

/// Last-good feed, persisted to Application Support.
///
/// The feed cache lets a relaunch show stories when the network is unavailable.
/// It is scoped to the feed URL so a former custom feed cannot populate the
/// official catalog. Audio itself is not downloaded here.
enum StoryCache {
    struct Feed: Codable {
        let schemaVersion: Int
        let sourceURL: String
        let stories: [Story]
        let cachedAt: Date
    }
    static let schemaVersion = 2

    private static let folder: URL = {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSTemporaryDirectory())
        let directory = base.appendingPathComponent("SoundScience", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory
    }()

    private static var feedFile: URL { folder.appendingPathComponent("feed.json") }
    private static var pinnedFile: URL { folder.appendingPathComponent("pinned.json") }

    static func saveFeed(_ stories: [Story], sourceURL: String) {
        guard let data = try? JSONEncoder().encode(
            Feed(schemaVersion: schemaVersion, sourceURL: sourceURL, stories: stories, cachedAt: .now)) else { return }
        try? data.write(to: feedFile, options: .atomic)
    }

    static func decodeFeed(_ data: Data, for sourceURL: String) -> Feed? {
        guard let feed = try? JSONDecoder().decode(Feed.self, from: data),
              feed.schemaVersion == schemaVersion,
              feed.sourceURL == sourceURL else { return nil }
        return feed
    }

    static func loadFeed(for sourceURL: String) -> Feed? {
        guard let data = try? Data(contentsOf: feedFile) else { return nil }
        return decodeFeed(data, for: sourceURL)
    }

    static func removeLegacyPins() {
        try? FileManager.default.removeItem(at: pinnedFile)
    }
}
