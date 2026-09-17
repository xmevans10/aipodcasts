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

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 30) {
                    header
                    if let story = continueStory { continueCard(story) }
                    showsSection
                    latestSection
                    statsSection
                    Label("Every episode cites its sources. Hosts and narration are AI-generated.", systemImage: "checkmark.seal")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
                .padding(.horizontal, 20).padding(.top, 6).padding(.bottom, 24)
            }
            .background(Theme.canvas)
            .toolbar(.hidden, for: .navigationBar)
            .refreshable { await library.refresh() }
            .sheet(isPresented: $settings) { SettingsView() }
        }
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 6) {
                Text(Date.now.formatted(.dateTime.weekday(.wide).month(.wide).day())).font(.subheadline).foregroundStyle(Theme.secondary)
                Text(greeting).font(Theme.display).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
                Text(summary).font(.subheadline).foregroundStyle(Theme.secondary)
            }
            Spacer()
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

    private func continueCard(_ story: Story) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Continue listening").font(.caption.weight(.semibold)).foregroundStyle(Theme.secondary)
            HStack(spacing: 14) {
                NavigationLink { EpisodeView(story: story) } label: {
                    HStack(spacing: 14) {
                        ShowCover(show: story.show).frame(width: 64)
                        VStack(alignment: .leading, spacing: 6) {
                            Text(story.show.title).font(.caption).foregroundStyle(Theme.secondary)
                            Text(story.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).lineLimit(2).multilineTextAlignment(.leading)
                            ProgressView(value: player.progress(of: story)).tint(Theme.ink)
                            Text("\(player.minutesLeft(of: story)) min left").font(.caption).foregroundStyle(Theme.secondary)
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
        VStack(alignment: .leading, spacing: 14) {
            SectionHeader(title: "Your shows") { NavigationLink("Browse") { BrowseView(embedded: true) } }
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)], spacing: 20) {
                ForEach(shows) { show in
                    NavigationLink { ShowView(show: show) } label: { ShowCard(show: show) }.buttonStyle(.plain)
                }
            }
        }
    }

    private var latestSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            SectionHeader(title: "Latest episodes") {
                if !unplayed.isEmpty {
                    Button { player.playEdition(unplayed) } label: { Label("Play all", systemImage: "play.fill") }
                        .accessibilityLabel("Play all unplayed episodes")
                }
            }
            if episodes.isEmpty {
                Text("New episodes will appear here after editorial review.").font(.subheadline).foregroundStyle(Theme.secondary).padding(.vertical, 12)
            }
            ForEach(Array(episodes.enumerated()), id: \.element.id) { index, story in
                EpisodeRow(story: story)
                if index < episodes.count - 1 { Divider().overlay(Theme.hairline) }
            }
            if let error = library.error { Text(error).font(.caption).foregroundStyle(.red) }
        }
    }

    private var statsSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            SectionHeader(title: "Your listening")
            HStack(alignment: .top, spacing: 10) {
                StatTile(value: "\(player.minutesThisWeek)", label: "min this week", symbol: "headphones")
                StatTile(value: "\(player.listening.completed.count)", label: "finished", symbol: "checkmark.circle")
                StatTile(value: "\(player.streakDays)", label: "day streak", symbol: "flame")
            }
        }
    }
}
