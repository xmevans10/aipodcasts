import SwiftUI

/// Circular play/pause control that reflects whether this episode is the one playing.
struct PlayButton: View {
    @EnvironmentObject var player: AudioPlayer
    var story: Story
    var size: CGFloat = 38
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private var active: Bool { player.story?.id == story.id && player.playing }
    var body: some View {
        Button {
            Haptics.tap()
            player.story?.id == story.id ? player.toggle() : player.play(story)
        } label: {
            Image(systemName: active ? "pause.fill" : "play.fill")
                .font(.system(size: size * 0.36, weight: .semibold))
                .contentTransition(reduceMotion ? .identity : .symbolEffect(.replace))
                .foregroundStyle(.white).frame(width: size, height: size)
                .background(Circle().fill(LinearGradient(colors: active ? [story.show.mid, story.show.dark] : [Theme.ink, Theme.ink],
                                                         startPoint: .topLeading, endPoint: .bottomTrailing)))
                .frame(minWidth: 44, minHeight: 44)
                .contentShape(Rectangle())
        }
        .buttonStyle(PressableStyle(scale: 0.9))
        .animation(Motion.standard(reduceMotion: reduceMotion), value: active)
        .accessibilityLabel(active ? "Pause \(story.title)" : "Play \(story.title)")
    }
}

/// Listening status line: date · length, or progress / played.
struct EpisodeMeta: View {
    @EnvironmentObject var player: AudioPlayer
    var story: Story
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var body: some View {
        let progress = player.progress(of: story)
        HStack(spacing: 6) {
            if !story.dateText.isEmpty { Text(story.dateText) ; Text("·") }
            if progress >= 1 {
                Label("Played", systemImage: "checkmark").labelStyle(.titleAndIcon)
            } else if progress > 0 {
                Capsule().fill(Theme.hairline).frame(width: 36, height: 4)
                    .overlay(alignment: .leading) { Capsule().fill(story.show.mid).frame(width: 36 * progress, height: 4)
                        .animation(Motion.standard(reduceMotion: reduceMotion), value: progress) }
                Text("\(player.minutesLeft(of: story)) min left")
            } else {
                Text("\(story.minutes) min")
            }
        }
        .font(.caption).foregroundStyle(Theme.secondary)
    }
}

/// Standard episode row: cover, show, title, status and a play button.
struct EpisodeRow: View {
    var story: Story
    var showsShow = true
    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            NavigationLink { EpisodeView(story: story) } label: {
                HStack(alignment: .top, spacing: 14) {
                    ShowCover(show: story.show).frame(width: 60)
                    VStack(alignment: .leading, spacing: 5) {
                        if showsShow {
                            Text(story.show.title.uppercased()).font(.caption2.weight(.semibold)).tracking(0.6).foregroundStyle(Theme.secondary)
                        }
                        Text(story.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
                            .multilineTextAlignment(.leading).lineLimit(2)
                        EpisodeMeta(story: story)
                    }
                    Spacer(minLength: 0)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(PressableStyle(scale: 0.98))
            PlayButton(story: story)
        }
        .padding(.vertical, 10)
    }
}

/// Grid card for a show, used on Home and in onboarding.
/// It is meant to sit inside a `NavigationLink` / `Button` styled with `.buttonStyle(.pressable)`,
/// which gives it the shared press-down scale and dim.
struct ShowCard: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    var show: Show
    private var episodes: [Story] { library.episodes(of: show) }
    private var unplayed: Int { episodes.filter { player.progress(of: $0) == 0 }.count }
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            ShowCover(show: show)
                .overlay(alignment: .topLeading) {
                    if unplayed > 0 {
                        Text("\(unplayed) NEW").font(.system(size: 10, weight: .bold)).tracking(0.5)
                            .padding(.horizontal, 8).padding(.vertical, 4).background(.white, in: Capsule())
                            .foregroundStyle(show.dark).padding(10)
                            .contentTransition(.numericText(value: Double(unplayed)))
                            .transition(reduceMotion ? .opacity : .scale(scale: 0.6, anchor: .topLeading).combined(with: .opacity))
                    }
                }
                .animation(Motion.standard(reduceMotion: reduceMotion), value: unplayed)
            VStack(alignment: .leading, spacing: 1) {
                Text(show.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).lineLimit(1)
                Text(show.host.name).font(.caption).foregroundStyle(Theme.secondary).lineLimit(1)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(show.title), hosted by \(show.host.name)\(unplayed > 0 ? ", \(unplayed) new" : "")")
    }
}
