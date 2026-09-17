import SwiftUI

struct QueueView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    private var suggestions: [Story] {
        library.latest.filter { $0.id != player.story?.id && !player.listening.queue.contains($0.id) && player.progress(of: $0) < 1 }
    }
    var body: some View {
        List {
            if let current = player.story {
                Section("Now playing") {
                    HStack(spacing: 12) {
                        ShowCover(show: current.show).frame(width: 44)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(current.title).font(.subheadline.weight(.semibold)).lineLimit(2)
                            Text(current.show.title).font(.caption).foregroundStyle(Theme.secondary)
                        }
                        Spacer()
                        Button { player.toggle() } label: { Image(systemName: player.playing ? "pause.fill" : "play.fill").frame(width: 44, height: 44) }
                            .buttonStyle(.borderless).accessibilityLabel(player.playing ? "Pause" : "Play")
                    }
                }
            }
            Section("Up next · \(player.queuedStories.count)") {
                if player.queuedStories.isEmpty {
                    Text("Nothing queued. Add an episode below or from its page.").font(.subheadline).foregroundStyle(Theme.secondary).padding(.vertical, 8)
                }
                ForEach(player.queuedStories) { story in
                    HStack(spacing: 12) {
                        ShowCover(show: story.show).frame(width: 40)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(story.title).font(.subheadline.weight(.semibold)).lineLimit(2)
                            Text("\(story.show.title) · \(story.minutes) min").font(.caption).foregroundStyle(Theme.secondary)
                        }
                        Spacer()
                        Menu {
                            Button("Play now", systemImage: "play.fill") { player.play(story) }
                            Button("Move up", systemImage: "arrow.up") { player.moveQueued(story.id, by: -1) }.disabled(player.queuedStories.first?.id == story.id)
                            Button("Move down", systemImage: "arrow.down") { player.moveQueued(story.id, by: 1) }.disabled(player.queuedStories.last?.id == story.id)
                            Button("Remove", systemImage: "minus.circle", role: .destructive) { player.removeQueued(story.id) }
                        } label: { Image(systemName: "ellipsis").frame(width: 44, height: 44) }.accessibilityLabel("Queue options for \(story.title)")
                    }
                    .swipeActions { Button("Remove", role: .destructive) { player.removeQueued(story.id) } }
                }
            }
            if !suggestions.isEmpty {
                Section("Suggested") {
                    ForEach(suggestions) { story in
                        HStack(spacing: 12) {
                            ShowCover(show: story.show).frame(width: 40)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(story.title).font(.subheadline).lineLimit(2)
                                Text("\(story.show.title) · \(story.minutes) min").font(.caption).foregroundStyle(Theme.secondary)
                            }
                            Spacer()
                            Button { player.enqueue(story) } label: { Image(systemName: "plus.circle").font(.title2).frame(width: 44, height: 44) }
                                .buttonStyle(.borderless).accessibilityLabel("Add \(story.title) to queue")
                        }
                    }
                }
            }
        }
        .scrollContentBackground(.hidden).background(Theme.canvas)
        .navigationTitle("Up next").navigationBarTitleDisplayMode(.inline)
        .toolbar { if !player.queuedStories.isEmpty { Button("Clear") { player.clearQueue() } } }
    }
}
