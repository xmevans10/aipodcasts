import SwiftUI

struct HomeView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @State private var settings = false

    private var greeting: String {
        switch Calendar.current.component(.hour, from: .now) {
        case 5..<12: "Good morning"
        case 12..<17: "Good afternoon"
        default: "Good evening"
        }
    }
    /// Followed shows first, then the rest, in catalogue order.
    private var shows: [Show] { Show.all.filter { library.isFollowing($0) } + Show.all.filter { !library.isFollowing($0) } }
    private var episodes: [Story] { library.latest }
    private var freshThisWeek: [Story] {
        let cutoff = Calendar.current.date(byAdding: .day, value: -7, to: .now) ?? .distantPast
        return episodes.filter { ($0.publishedDate ?? .distantPast) >= cutoff }
    }
    private var continueStory: Story? {
        if let current = player.story, player.progress(of: current) < 1, !player.isPreview { return current }
        return library.latest.first { let p = player.progress(of: $0); return p > 0 && p < 1 }
    }
    private var unplayed: [Story] { episodes.filter { player.progress(of: $0) < 1 } }
    /// The newest episode not yet started, and not already shown in "Continue listening".
    private var featured: Story? {
        episodes.first { player.progress(of: $0) == 0 && $0.id != continueStory?.id }
            ?? unplayed.first { $0.id != continueStory?.id }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 36) {
                    header
                    if library.isOffline { offlineBanner }
                    if let story = featured { FeaturedEpisodeCard(story: story) }
                    if let story = continueStory { continueCard(story) }
                    showsSection
                    latestSection
                    statsSection
                    Label("Every episode cites its sources. Hosts and narration are AI-generated.", systemImage: "checkmark.seal")
                        .typeStyle(.meta).foregroundStyle(Theme.secondary)
                }
                .padding(.horizontal, 20).padding(.top, 6).padding(.bottom, 24)
            }
            .background(Theme.canvas)
            .toolbar(.hidden, for: .navigationBar)
            .refreshable { await library.refresh() }
            .task { await library.refresh() }
            .sheet(isPresented: $settings) { SettingsView() }
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 8) {
                Text(Date.now.formatted(.dateTime.weekday(.wide).month(.wide).day()))
                    .typeStyle(.overline).foregroundStyle(Theme.secondary)
                Text(greeting).typeStyle(.largeTitle).foregroundStyle(Theme.ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityAddTraits(.isHeader)
                Text(summary).typeStyle(.body).foregroundStyle(Theme.secondary)
            }
            Spacer(minLength: 12)
            Button { settings = true } label: {
                Image(systemName: "gearshape").font(.body.weight(.medium)).foregroundStyle(Theme.ink)
                    .frame(width: 40, height: 40).background(Theme.surface, in: Circle()).overlay(Circle().strokeBorder(Theme.hairline))
            }.accessibilityLabel("Settings").frame(minWidth: 44, minHeight: 44)
        }
    }

    private var summary: String {
        let count = freshThisWeek.count
        guard count > 0 else { return "Catch up on the latest from your shows." }
        let minutes = freshThisWeek.reduce(0) { $0 + $1.minutes }
        return "\(count) new episode\(count == 1 ? "" : "s") this week · \(minutes) min"
    }

    private var offlineBanner: some View {
        HStack(spacing: 12) {
            Image(systemName: "wifi.slash").font(.body.weight(.semibold)).foregroundStyle(Theme.ink)
                .frame(width: 36, height: 36).background(Theme.subtle, in: Circle())
            VStack(alignment: .leading, spacing: 2) {
                Text("You're offline").typeStyle(.headline).foregroundStyle(Theme.ink)
                Text(cachedText).typeStyle(.meta).foregroundStyle(Theme.secondary)
            }
            Spacer(minLength: 8)
            Button(library.loading ? "Retrying…" : "Retry") { Task { await library.refresh() } }
                .font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).disabled(library.loading)
        }
        .padding(14)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous).strokeBorder(Theme.hairline))
        .accessibilityElement(children: .combine)
    }

    private var cachedText: String {
        guard let date = library.feedCachedAt else { return "Showing your saved episodes." }
        return "Last updated \(date.formatted(.relative(presentation: .named)))."
    }

    private func continueCard(_ story: Story) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Continue listening").typeStyle(.overline).foregroundStyle(Theme.secondary)
            HStack(spacing: 14) {
                NavigationLink { EpisodeView(story: story) } label: {
                    HStack(spacing: 14) {
                        ShowCover(show: story.show).frame(width: 64)
                        VStack(alignment: .leading, spacing: 6) {
                            Text(story.show.title).typeStyle(.meta).foregroundStyle(Theme.secondary)
                            Text(story.title).typeStyle(.headline).foregroundStyle(Theme.ink).lineLimit(2).multilineTextAlignment(.leading)
                            ProgressView(value: player.progress(of: story)).tint(story.show.mid)
                            Text("\(player.minutesLeft(of: story)) min left").typeStyle(.meta).foregroundStyle(Theme.secondary)
                        }
                        Spacer(minLength: 0)
                    }.contentShape(Rectangle())
                }.buttonStyle(.plain)
                PlayButton(story: story, size: 44)
            }
        }
        .card()
    }

    private var showsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HomeSectionHeader(title: "Your shows") { NavigationLink("Browse") { BrowseView(embedded: true) } }
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)], spacing: 20) {
                ForEach(shows) { show in
                    NavigationLink { ShowView(show: show) } label: { ShowCard(show: show) }.buttonStyle(.pressable)
                }
            }
        }
    }

    private var latestSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            HomeSectionHeader(title: "Latest episodes") {
                if !unplayed.isEmpty {
                    Button { player.playEdition(unplayed) } label: { Label("Play all", systemImage: "play.fill") }
                        .accessibilityLabel("Play all unplayed episodes")
                }
            }
            .padding(.bottom, 4)
            if episodes.isEmpty {
                Text("New episodes will appear here after editorial review.").typeStyle(.body).foregroundStyle(Theme.secondary).padding(.vertical, 12)
            }
            ForEach(Array(episodes.enumerated()), id: \.element.id) { index, story in
                EpisodeRow(story: story)
                if index < episodes.count - 1 { Divider().overlay(Theme.hairline) }
            }
            if let error = library.error { Text(error).typeStyle(.meta).foregroundStyle(.red) }
        }
    }

    private var statsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            HomeSectionHeader(title: "Your listening")
            HStack(alignment: .top, spacing: 10) {
                HomeStat(value: "\(player.minutesThisWeek)", label: "min this week", symbol: "headphones")
                HomeStat(value: "\(player.listening.completed.count)", label: "finished", symbol: "checkmark.circle")
                HomeStat(value: "\(player.streakDays)", label: "day streak", symbol: "flame")
            }
        }
    }
}

// MARK: - Featured episode hero

/// Full-bleed hero for the newest unplayed episode: the show's gradient, the host large,
/// the title at hero size. Tapping the card opens the player; the play button toggles it.
private struct FeaturedEpisodeCard: View {
    @EnvironmentObject var player: AudioPlayer
    var story: Story
    @ScaledMetric(relativeTo: .largeTitle) private var avatarSize: CGFloat = 84
    @ScaledMetric(relativeTo: .largeTitle) private var playSize: CGFloat = 64

    private var show: Show { story.show }
    private var isCurrent: Bool { player.story?.id == story.id }
    private var active: Bool { isCurrent && player.playing }
    private var shape: RoundedRectangle { RoundedRectangle(cornerRadius: OpenAIKit.Radius.hero, style: .continuous) }

    private func togglePlayback() { isCurrent ? player.toggle() : player.play(story) }
    private func openPlayer() {
        if !isCurrent { player.play(story) }
        player.isPlayerPresented = true
    }

    var body: some View {
        Button(action: openPlayer) {
            VStack(alignment: .leading, spacing: 0) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("New episode").typeStyle(.overline).foregroundStyle(.white.opacity(0.8))
                        Text(show.title).typeStyle(.overline).foregroundStyle(.white)
                    }
                    .shadow(color: show.dark.opacity(0.5), radius: 6)
                    Spacer(minLength: 12)
                    HostAvatar(host: story.host, size: avatarSize)
                        .overlay(Circle().strokeBorder(.white.opacity(0.85), lineWidth: 2.5))
                        .shadow(color: show.dark.opacity(0.45), radius: 12, y: 4)
                }
                Spacer(minLength: 28)
                Text(story.title).typeStyle(.hero).foregroundStyle(.white)
                    .lineLimit(4).minimumScaleFactor(0.6)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Text(story.dek).typeStyle(.body).foregroundStyle(.white.opacity(0.9))
                    .lineLimit(2).multilineTextAlignment(.leading)
                    .padding(.top, 10)
                // Room for the play / details row laid over the bottom edge.
                Color.clear.frame(height: playSize + 18)
            }
            .padding(22)
            .frame(maxWidth: .infinity, minHeight: 340, alignment: .leading)
            .background { background }
            .clipShape(shape)
            .contentShape(shape)
        }
        .buttonStyle(HeroPressStyle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Featured episode from \(show.title): \(story.title). \(story.dek). \(story.minutes) minutes.")
        .accessibilityHint("Opens the player")
        .accessibilityAddTraits(.isButton)
        .overlay(alignment: .bottom) { controls.padding(22) }
        .shadow(color: show.dark.opacity(0.28), radius: 20, y: 10)
    }

    private var background: some View {
        ZStack {
            LinearGradient(colors: [show.light, show.mid, show.dark], startPoint: .topTrailing, endPoint: .bottomLeading)
            RadialGradient(colors: [show.light.opacity(0.65), .clear], center: UnitPoint(x: 0.9, y: 0.05),
                           startRadius: 0, endRadius: 260)
            // Scrim: keeps the white title and dek legible where the gradient runs light.
            LinearGradient(colors: [.clear, show.dark.opacity(0.35), .black.opacity(0.35)],
                           startPoint: UnitPoint(x: 0.5, y: 0.25), endPoint: .bottom)
        }
    }

    private var controls: some View {
        HStack(alignment: .center, spacing: 12) {
            Button(action: togglePlayback) {
                Image(systemName: active ? "pause.fill" : "play.fill")
                    .font(.system(size: playSize * 0.36, weight: .bold))
                    .foregroundStyle(show.dark)
                    .offset(x: active ? 0 : playSize * 0.03)
                    .frame(width: playSize, height: playSize)
                    .background(.white, in: Circle())
                    .shadow(color: .black.opacity(0.2), radius: 8, y: 3)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(active ? "Pause \(story.title)" : "Play \(story.title)")

            VStack(alignment: .leading, spacing: 2) {
                Text("\(story.minutes) min").typeStyle(.headline).foregroundStyle(.white)
                if !story.dateText.isEmpty {
                    Text(story.dateText).typeStyle(.meta).foregroundStyle(.white.opacity(0.85))
                }
            }
            .accessibilityElement(children: .combine)

            Spacer(minLength: 8)

            NavigationLink { EpisodeView(story: story) } label: {
                HStack(spacing: 4) {
                    Text("Details")
                    Image(systemName: "chevron.right").font(.caption.weight(.bold))
                }
                .typeStyle(.headline)
                .foregroundStyle(.white)
                .padding(.horizontal, 16)
                .frame(minHeight: 44)
                .background(.white.opacity(0.18), in: Capsule())
                .overlay(Capsule().strokeBorder(.white.opacity(0.35)))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Episode details for \(story.title)")
        }
    }
}

private struct HeroPressStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.snappy(duration: 0.18), value: configuration.isPressed)
    }
}

// MARK: - Home-scale building blocks

/// Section header at the `title` step: serif, larger and heavier than the rows beneath it.
private struct HomeSectionHeader<Trailing: View>: View {
    var title: String
    @ViewBuilder var trailing: Trailing
    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title).typeStyle(.title).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
            Spacer()
            trailing.font(.subheadline.weight(.semibold)).foregroundStyle(Theme.secondary)
        }
    }
}
private extension HomeSectionHeader where Trailing == EmptyView {
    init(title: String) { self.title = title; self.trailing = EmptyView() }
}

/// Stat tile with a big rounded numeral and a quiet overline label.
private struct HomeStat: View {
    var value: String
    var label: String
    var symbol: String
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: symbol).font(.footnote.weight(.semibold)).foregroundStyle(Theme.secondary)
            Text(value).typeStyle(.numeral).foregroundStyle(Theme.ink).lineLimit(1).minimumScaleFactor(0.6)
            Text(label).typeStyle(.overline).foregroundStyle(Theme.secondary).lineLimit(1).minimumScaleFactor(0.7)
        }
        .padding(14).frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous).strokeBorder(Theme.hairline))
        .accessibilityElement(children: .combine)
    }
}
