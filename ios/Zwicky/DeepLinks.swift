import Foundation

/// Recognizes only episode URLs belonging to this app's published feed origin.
struct EpisodeLink: Equatable {
    let id: String

    static func parse(_ url: URL, feedURL: URL) -> EpisodeLink? {
        guard let incoming = URLComponents(url: url, resolvingAgainstBaseURL: false),
              incoming.user == nil, incoming.password == nil, incoming.port == nil,
              let scheme = incoming.scheme?.lowercased() else { return nil }

        let rawID: String
        if scheme == "zwicky" {
            guard incoming.host?.lowercased() == "episode", incoming.query == nil,
                  incoming.fragment == nil, incoming.percentEncodedPath.hasPrefix("/") else { return nil }
            rawID = String(incoming.percentEncodedPath.dropFirst())
        } else if scheme == "https" {
            guard let feed = URLComponents(url: feedURL, resolvingAgainstBaseURL: false),
                  feed.scheme?.lowercased() == "https", incoming.host?.lowercased() == feed.host?.lowercased(),
                  feed.port == nil else { return nil }
            let prefix = (feed.percentEncodedPath as NSString).deletingLastPathComponent
            let leadingPath = prefix + "/listen/"
            guard incoming.percentEncodedPath.hasPrefix(leadingPath),
                  incoming.percentEncodedPath.hasSuffix(".html") else { return nil }
            rawID = String(incoming.percentEncodedPath.dropFirst(leadingPath.count).dropLast(5))
        } else {
            return nil
        }

        // Publisher IDs are ASCII slugs. Reject encoded separators and traversal rather
        // than decoding a second, potentially different, path into an episode ID.
        guard !rawID.isEmpty, rawID.count <= 160,
              let first = rawID.utf8.first, first.isASCIILowercaseOrDigit,
              rawID.utf8.allSatisfy({ $0.isASCIILowercaseOrDigit || $0 == 45 || $0 == 46 || $0 == 95 })
        else { return nil }
        return EpisodeLink(id: rawID)
    }
}

private extension UInt8 {
    var isASCIILowercaseOrDigit: Bool { (97...122).contains(self) || (48...57).contains(self) }
}
