import SwiftUI

struct QueueView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    private var suggestions: [Story] {
        library.stories.filter { $0.id != player.story?.id && !player.listening.queue.contains($0.id) }
    }
    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Stay in your orbit.").font(.system(size: 30, design: .serif))
                    Text("Stories play in order. Make a little room for whatever catches your curiosity.").font(.subheadline).foregroundStyle(ScienceBreak.muted)
                }.padding(.vertical, 8)
            }.listRowBackground(Color.clear)
            if let current = player.story {
                Section("Now in your ears") {
                    HStack {
                        HostAvatar(host: current.host, size: 38)
                        Text(current.title).font(.subheadline.weight(.semibold))
                        Spacer()
                        Button { player.toggle() } label: { Image(systemName: player.playing ? "pause.fill" : "play.fill").frame(width: 44, height: 44) }
                            .buttonStyle(.borderless).accessibilityLabel(player.playing ? "Pause" : "Play")
                    }
                }
            }
            Section("Up next · \(player.queuedStories.count)") {
                if player.queuedStories.isEmpty {
                    Text("A little breathing room. Add a story below or from its article.").font(.subheadline).foregroundStyle(ScienceBreak.muted).padding(.vertical, 12)
                }
                ForEach(player.queuedStories) { story in
                    HStack(spacing: 12) {
                        HostAvatar(host: story.host, size: 34)
                        VStack(alignment: .leading, spacing: 5) {
                            Text(story.title).font(.subheadline.weight(.semibold))
                            Text("\(story.host.name) · \(story.minutes) min").font(.caption).foregroundStyle(ScienceBreak.muted)
                        }
                        Spacer()
                        Menu {
                            Button("Play now", systemImage: "play.fill") { player.play(story) }
                            Button("Move up", systemImage: "arrow.up") { player.moveQueued(story.id, by: -1) }.disabled(player.queuedStories.first?.id == story.id)
                            Button("Move down", systemImage: "arrow.down") { player.moveQueued(story.id, by: 1) }.disabled(player.queuedStories.last?.id == story.id)
                            Button("Remove", systemImage: "minus.circle", role: .destructive) { player.removeQueued(story.id) }
                        } label: { Image(systemName: "ellipsis").frame(width: 44, height: 44) }.accessibilityLabel("Queue options for \(story.title)")
                    }.padding(.vertical, 6)
                    .swipeActions { Button("Remove", role: .destructive) { player.removeQueued(story.id) } }
                }
            }
            if !suggestions.isEmpty {
                Section("A little more wonder") {
                    ForEach(suggestions) { story in
                        HStack {
                            VStack(alignment: .leading, spacing: 5) { Text(story.title).font(.subheadline); Text("\(story.topic.capitalized) · \(story.minutes) min").font(.caption).foregroundStyle(ScienceBreak.muted) }
                            Spacer()
                            Button { player.enqueue(story) } label: { Image(systemName: "plus.circle.fill").font(.title2).frame(width: 44, height: 44) }.buttonStyle(.borderless).accessibilityLabel("Add \(story.title) to queue")
                        }.padding(.vertical, 4)
                    }
                }
            }
        }.scrollContentBackground(.hidden).background(ScienceBreak.paper).navigationTitle("Your queue").navigationBarTitleDisplayMode(.inline)
            .toolbar { if !player.queuedStories.isEmpty { Button("Clear") { player.clearQueue() } } }
    }
}
