import SwiftUI

struct QueueView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    private var rowLayout: AnyLayout {
        dynamicTypeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: .leading, spacing: 12))
            : AnyLayout(HStackLayout(spacing: 12))
    }
    private var suggestions: [Story] {
        library.latest.filter { $0.id != player.story?.id && !player.listening.queue.contains($0.id) && player.progress(of: $0) < 1 }
    }
    var body: some View {
        List {
            if let current = player.story {
                Section("Now playing") {
                    rowLayout {
                        ShowCover(show: current.show).frame(width: 44).accessibilityHidden(true)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(current.title).font(.subheadline.weight(.semibold)).lineLimit(dynamicTypeSize.isAccessibilitySize ? nil : 2)
                            Text(current.show.title).font(.caption).foregroundStyle(Theme.secondary)
                        }
                        .accessibilityElement(children: .combine)
                        if !dynamicTypeSize.isAccessibilitySize { Spacer() }
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
                    rowLayout {
                        ShowCover(show: story.show).frame(width: 40).accessibilityHidden(true)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(story.title).font(.subheadline.weight(.semibold)).lineLimit(dynamicTypeSize.isAccessibilitySize ? nil : 2)
                            Text("\(story.show.title) · \(story.minutes) min").font(.caption).foregroundStyle(Theme.secondary)
                        }
                        .accessibilityElement(children: .combine)
                        if !dynamicTypeSize.isAccessibilitySize { Spacer() }
                        Menu {
                            Button("Play now", systemImage: "play.fill") { player.play(story) }
                            Button("Move up", systemImage: "arrow.up") { player.moveQueued(story.id, by: -1) }.disabled(player.queuedStories.first?.id == story.id)
                            Button("Move down", systemImage: "arrow.down") { player.moveQueued(story.id, by: 1) }.disabled(player.queuedStories.last?.id == story.id)
                            Button("Remove", systemImage: "minus.circle", role: .destructive) { player.removeQueued(story.id) }
                        } label: { Image(systemName: "ellipsis").frame(width: 44, height: 44) }.accessibilityLabel("Queue options for \(story.title)")
                    }
                    .swipeActions { Button("Remove", role: .destructive) { player.removeQueued(story.id) }.accessibilityHint("Removes \(story.title) from your queue") }
                }
            }
            if !suggestions.isEmpty {
                Section("Suggested") {
                    ForEach(suggestions) { story in
                        rowLayout {
                            ShowCover(show: story.show).frame(width: 40).accessibilityHidden(true)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(story.title).font(.subheadline).lineLimit(dynamicTypeSize.isAccessibilitySize ? nil : 2)
                                Text("\(story.show.title) · \(story.minutes) min").font(.caption).foregroundStyle(Theme.secondary)
                            }
                            .accessibilityElement(children: .combine)
                            if !dynamicTypeSize.isAccessibilitySize { Spacer() }
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
