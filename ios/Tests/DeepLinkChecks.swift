import Foundation

@main enum DeepLinkChecks {
    static func main() {
        let feed = URL(string: "https://cdn.example/v1/feed.json")!
        func episode(_ raw: String) -> String? {
            guard let url = URL(string: raw) else { return nil }
            return EpisodeLink.parse(url, feedURL: feed)?.id
        }

        precondition(episode("https://cdn.example/v1/listen/episode-webwork-1.html") == "episode-webwork-1")
        precondition(episode("https://cdn.example/v1/listen/episode-1.html?source=share") == "episode-1")
        precondition(episode("zwicky://episode/episode-webwork-1") == "episode-webwork-1")
        precondition(episode("https://other.example/v1/listen/episode-1.html") == nil)
        precondition(episode("http://cdn.example/v1/listen/episode-1.html") == nil)
        precondition(episode("https://user@cdn.example/v1/listen/episode-1.html") == nil)
        precondition(episode("https://cdn.example:444/v1/listen/episode-1.html") == nil)
        precondition(episode("https://cdn.example/v1/listen/%2Fsecret.html") == nil)
        precondition(episode("https://cdn.example/v1/listen/../secret.html") == nil)
        precondition(episode("https://cdn.example/v1/listen/episode-1.mp3") == nil)
        precondition(episode("zwicky://episode/episode-1/extra") == nil)
        precondition(episode("zwicky://other/episode-1") == nil)
        print("Deep link checks passed")
    }
}
