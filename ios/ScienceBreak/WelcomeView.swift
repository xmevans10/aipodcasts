import SwiftUI

/// Four short steps: what this is, which shows to follow, a daily goal, and a first episode.
struct WelcomeView: View {
    @AppStorage("onboarded") private var onboarded = false
    @EnvironmentObject private var library: Library
    @EnvironmentObject private var player: AudioPlayer
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var step = 0
    @State private var selected: Set<String> = Set(Show.all.map(\.id))
    @AccessibilityFocusState private var headingFocused: Bool

    private var firstEpisode: Story? {
        library.latest.first { selected.contains($0.hostID) && !$0.isDemo } ?? library.latest.first { selected.contains($0.hostID) }
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    switch step {
                    case 0: intro
                    case 1: pickShows
                    case 2: pickGoal
                    default: firstListen
                    }
                }
                .padding(.horizontal, 24).padding(.top, 12).padding(.bottom, 24)
                .frame(maxWidth: 600, alignment: .leading).frame(maxWidth: .infinity)
                .id(step).transition(.opacity.combined(with: .offset(y: reduceMotion ? 0 : 10)))
            }
            actions
        }
        .background(Theme.canvas.ignoresSafeArea())
        .foregroundStyle(Theme.ink)
        .interactiveDismissDisabled()
        .onAppear { player.pause() }
    }

    private var header: some View {
        HStack {
            if step > 0 {
                Button { go(to: step - 1) } label: { Image(systemName: "chevron.left").font(.body.weight(.semibold)).frame(width: 44, height: 44) }
                    .accessibilityLabel("Back")
            } else {
                Text("Sound Science").font(.system(size: 19, weight: .semibold, design: .serif)).frame(height: 44)
            }
            Spacer()
            HStack(spacing: 6) {
                ForEach(0..<4) { index in
                    Capsule().fill(index <= step ? Theme.ink : Theme.hairline).frame(width: index == step ? 22 : 6, height: 6)
                }
            }.accessibilityElement(children: .ignore).accessibilityLabel("Step \(step + 1) of 4")
            Spacer()
            Button("Skip") { finish(play: false) }.font(.subheadline).foregroundStyle(Theme.secondary).frame(minWidth: 44, minHeight: 44)
        }
        .padding(.horizontal, 20).padding(.top, 6)
    }

    private func title(_ text: String) -> some View {
        Text(text).font(.system(size: 34, weight: .semibold, design: .serif)).fixedSize(horizontal: false, vertical: true)
            .accessibilityAddTraits(.isHeader).accessibilityFocused($headingFocused)
    }

    private var intro: some View {
        Group {
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)], spacing: 12) {
                ForEach(Show.all) { ShowCover(show: $0) }
            }
            title("Science worth\nlistening to.")
            Text("Short podcasts about new research, from four shows with their own hosts.")
                .font(.body).foregroundStyle(Theme.secondary)
            VStack(alignment: .leading, spacing: 14) {
                point("clock", "About three minutes an episode")
                point("checkmark.seal", "Every episode links to its sources")
                point("text.quote", "Read along as you listen")
            }
        }
    }

    private func point(_ symbol: String, _ text: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: symbol).font(.body.weight(.medium)).frame(width: 36, height: 36).background(Theme.subtle, in: Circle())
            Text(text).font(.subheadline)
        }
    }

    private var pickShows: some View {
        Group {
            title("Pick your shows")
            Text("Follow the ones that sound like you. You can change this anytime.").font(.body).foregroundStyle(Theme.secondary)
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)], spacing: 18) {
                ForEach(Show.all) { show in
                    let isOn = selected.contains(show.id)
                    Button {
                        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.15)) {
                            if isOn { selected.remove(show.id) } else { selected.insert(show.id) }
                        }
                    } label: {
                        VStack(alignment: .leading, spacing: 10) {
                            ShowCover(show: show)
                                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(isOn ? Theme.ink : .clear, lineWidth: 3))
                                .overlay(alignment: .topTrailing) {
                                    Image(systemName: isOn ? "checkmark.circle.fill" : "circle")
                                        .font(.title2).symbolRenderingMode(.palette)
                                        .foregroundStyle(isOn ? .white : .white.opacity(0.9), isOn ? Theme.ink : .clear).padding(10)
                                }
                            HStack(spacing: 8) {
                                HostAvatar(host: show.host, size: 26)
                                VStack(alignment: .leading, spacing: 1) {
                                    Text(show.title).font(.subheadline.weight(.semibold)).lineLimit(1)
                                    Text(show.category).font(.caption).foregroundStyle(Theme.secondary).lineLimit(1)
                                }
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(show.title), \(show.category), hosted by \(show.host.name)")
                    .accessibilityAddTraits(isOn ? .isSelected : [])
                }
            }
        }
    }

    private var pickGoal: some View {
        Group {
            title("How much, most days?")
            Text("A small daily goal keeps the streak honest. Episodes run about three minutes, so pick what fits your walk or commute.")
                .font(.body).foregroundStyle(Theme.secondary)
            VStack(spacing: 10) {
                ForEach(goalOptions, id: \.minutes) { option in
                    let isOn = library.dailyGoalMinutes == option.minutes
                    Button { library.dailyGoalMinutes = option.minutes } label: {
                        HStack(spacing: 14) {
                            Text("\(option.minutes)").font(.system(size: 20, weight: .semibold, design: .rounded)).monospacedDigit()
                                .frame(width: 46, height: 46).background(isOn ? Theme.ink : Theme.subtle, in: Circle())
                                .foregroundStyle(isOn ? .white : Theme.ink)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(option.title).font(.subheadline.weight(.semibold))
                                Text(option.detail).font(.caption).foregroundStyle(Theme.secondary)
                            }
                            Spacer(minLength: 0)
                            Image(systemName: isOn ? "checkmark.circle.fill" : "circle").font(.title3)
                                .foregroundStyle(isOn ? Theme.ink : Theme.tertiary.opacity(0.5))
                        }
                        .padding(14)
                        .background(Theme.surface, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))
                        .overlay(RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous).strokeBorder(isOn ? Theme.ink : Theme.hairline, lineWidth: isOn ? 1.5 : 1))
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(option.minutes) minutes a day, \(option.title)")
                    .accessibilityAddTraits(isOn ? .isSelected : [])
                }
            }
            Text("You can change this anytime in the You tab.").font(.caption).foregroundStyle(Theme.secondary)
        }
    }

    private var goalOptions: [(minutes: Int, title: String, detail: String)] {
        [(3, "One episode", "A single story with your coffee."),
         (10, "A short walk", "Three episodes, most days."),
         (20, "The commute", "A proper listening habit.")]
    }

    private var firstListen: some View {
        Group {
            title("Start with this one")
            if let story = firstEpisode {
                VStack(alignment: .leading, spacing: 16) {
                    ShowCover(show: story.show)
                    VStack(alignment: .leading, spacing: 8) {
                        HStack(spacing: 8) {
                            HostAvatar(host: story.host, size: 24)
                            Text("\(story.show.title) · \(story.host.name)").font(.caption).foregroundStyle(Theme.secondary)
                        }
                        Text(story.title).font(.system(size: 22, weight: .semibold, design: .serif))
                        Text(story.dek).font(.subheadline).foregroundStyle(Theme.secondary)
                        Text(story.isDemo ? "Device voice sample" : "\(story.minutes) min · AI-narrated · Sources included").font(.caption).foregroundStyle(Theme.secondary)
                    }
                }.card()
            } else {
                Text("Your shows are warming up. Browse what's available while new episodes are produced.").foregroundStyle(Theme.secondary)
            }
        }
    }

    private var actions: some View {
        VStack(spacing: 6) {
            Button {
                switch step {
                case 0, 1, 2: go(to: step + 1)
                default: finish(play: firstEpisode != nil)
                }
            } label: {
                Text(step == 0 ? "Get started"
                     : step == 1 ? (selected.isEmpty ? "Pick at least one show" : "Follow \(selected.count) show\(selected.count == 1 ? "" : "s")")
                     : step == 2 ? "Set \(library.dailyGoalMinutes) min a day"
                     : firstEpisode == nil ? "Go to home" : "Play episode")
            }
            .buttonStyle(PrimaryButtonStyle(fullWidth: true))
            .disabled(step == 1 && selected.isEmpty)
            .opacity(step == 1 && selected.isEmpty ? 0.4 : 1)
            if step == 3 && firstEpisode != nil {
                Button("Go to home") { finish(play: false) }.font(.subheadline).foregroundStyle(Theme.secondary).frame(minHeight: 44)
            }
        }
        .padding(.horizontal, 24).padding(.top, 10).padding(.bottom, 10)
        .frame(maxWidth: 600).frame(maxWidth: .infinity)
        .background(Theme.canvas)
    }

    private func go(to next: Int) {
        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.25)) { step = next }
        headingFocused = true
    }

    private func finish(play: Bool) {
        if !selected.isEmpty { library.setFollowing(selected) }
        if let first = Show.all.first(where: { selected.contains($0.id) }) { library.hostID = first.id }
        if play, let story = firstEpisode { player.play(story) }
        onboarded = true
    }
}
