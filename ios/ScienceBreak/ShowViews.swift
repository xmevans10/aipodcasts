import SwiftUI

struct ShowView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    var show: Show
    private var episodes: [Story] { library.episodes(of: show) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                VStack(spacing: 16) {
                    ShowCover(show: show).frame(width: 210).shadow(color: .black.opacity(0.14), radius: 22, y: 12)
                    VStack(spacing: 6) {
                        Text(show.category.uppercased()).font(.caption2.weight(.semibold)).tracking(0.8).foregroundStyle(Theme.secondary)
                        Text(show.title).font(Theme.display).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
                        HStack(spacing: 8) {
                            HostAvatar(host: show.host, size: 24)
                            Text("Hosted by \(show.host.name)").font(.subheadline).foregroundStyle(Theme.secondary)
                        }
                    }
                    Text(show.tagline).font(.body).foregroundStyle(Theme.ink)
                    HStack(spacing: 10) {
                        if let latest = episodes.first {
                            Button { player.story?.id == latest.id ? player.toggle() : player.play(latest) } label: {
                                Label(player.story?.id == latest.id && player.playing ? "Pause" : "Play latest", systemImage: player.story?.id == latest.id && player.playing ? "pause.fill" : "play.fill")
                            }.buttonStyle(PrimaryButtonStyle())
                        }
                        Button { library.toggleFollow(show) } label: {
                            Label(library.isFollowing(show) ? "Following" : "Follow", systemImage: library.isFollowing(show) ? "checkmark" : "plus")
                        }.buttonStyle(SecondaryButtonStyle())
                    }
                    Text(statsLine).font(.caption).foregroundStyle(Theme.secondary)
                }
                .multilineTextAlignment(.center).frame(maxWidth: .infinity)

                VStack(alignment: .leading, spacing: 4) {
                    SectionHeader(title: "Episodes")
                    ForEach(Array(episodes.enumerated()), id: \.element.id) { index, story in
                        EpisodeRow(story: story, showsShow: false)
                        if index < episodes.count - 1 { Divider().overlay(Theme.hairline) }
                    }
                    if episodes.isEmpty { Text("The first episode is in production.").font(.subheadline).foregroundStyle(Theme.secondary) }
                }

                VStack(alignment: .leading, spacing: 14) {
                    SectionHeader(title: "About the show")
                    Text(show.about).font(.subheadline).foregroundStyle(Theme.ink).lineSpacing(3)
                    Divider().overlay(Theme.hairline)
                    HStack(spacing: 12) {
                        HostAvatar(host: show.host, size: 52)
                        VStack(alignment: .leading, spacing: 3) {
                            Text(show.host.name).font(.subheadline.weight(.semibold))
                            Text(show.host.personality).font(.caption).foregroundStyle(Theme.secondary)
                        }
                    }
                    Text("\(show.host.name) is a fictional AI presenter, not a real scientist. Episodes use a synthetic voice and link to their original sources.")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
                .card()
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 28)
        }
        .background(Theme.canvas)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var statsLine: String {
        let real = episodes
        guard !real.isEmpty else { return episodes.isEmpty ? "New show" : "Sample episode available" }
        let minutes = real.reduce(0) { $0 + $1.minutes }
        var line = "\(real.count) episode\(real.count == 1 ? "" : "s") · \(minutes) min"
        if let date = real.first?.dateText, !date.isEmpty { line += " · Updated \(date)" }
        return line
    }
}

struct BrowseView: View {
    @EnvironmentObject var library: Library
    /// True when pushed inside another NavigationStack.
    var embedded = false
    @State private var search = ""

    private var shows: [Show] {
        guard !search.isEmpty else { return Show.all }
        return Show.all.filter { ($0.title + $0.category + $0.tagline + $0.host.name).localizedCaseInsensitiveContains(search) }
    }
    private var episodes: [Story] {
        library.latest.filter { search.isEmpty || ($0.title + $0.dek + $0.body + $0.show.title).localizedCaseInsensitiveContains(search) }
    }

    var body: some View {
        if embedded { content } else { NavigationStack { content } }
    }

    private var content: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                VStack(alignment: .leading, spacing: 4) {
                    SectionHeader(title: "Shows")
                    ForEach(shows) { show in
                        NavigationLink { ShowView(show: show) } label: {
                            HStack(spacing: 14) {
                                ShowCover(show: show).frame(width: 84)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(show.category.uppercased()).font(.caption2.weight(.semibold)).tracking(0.6).foregroundStyle(Theme.secondary)
                                    Text(show.title).font(.headline).foregroundStyle(Theme.ink)
                                    Text(show.tagline).font(.subheadline).foregroundStyle(Theme.secondary).lineLimit(2)
                                    HStack(spacing: 6) {
                                        HostAvatar(host: show.host, size: 20)
                                        Text(show.host.name).font(.caption).foregroundStyle(Theme.secondary)
                                    }
                                }.multilineTextAlignment(.leading)
                                Spacer(minLength: 0)
                                Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
                            }
                            .padding(.vertical, 10).contentShape(Rectangle())
                        }.buttonStyle(.plain)
                    }
                    if shows.isEmpty { Text("No shows match “\(search)”.").font(.subheadline).foregroundStyle(Theme.secondary) }
                }
                VStack(alignment: .leading, spacing: 4) {
                    SectionHeader(title: search.isEmpty ? "All episodes" : "Episodes")
                    ForEach(episodes) { EpisodeRow(story: $0) }
                    if episodes.isEmpty { Text("No episodes match “\(search)”.").font(.subheadline).foregroundStyle(Theme.secondary) }
                }
            }
            .padding(.horizontal, 20).padding(.bottom, 24)
        }
        .background(Theme.canvas)
        .navigationTitle("Browse")
        .searchable(text: $search, prompt: "Shows, hosts, topics")
    }
}

struct LibraryView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @State private var selection = 0
    private var items: [Story] {
        library.latest.filter {
            switch selection {
            case 0: return library.saved.contains($0.id)
            case 1: let p = player.progress(of: $0); return p > 0 && p < 1
            default: return player.progress(of: $0) >= 1
            }
        }
    }
    private var followed: [Show] { Show.all.filter { library.isFollowing($0) } }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    VStack(alignment: .leading, spacing: 14) {
                        SectionHeader(title: "Following")
                        if followed.isEmpty {
                            Text("Follow a show to keep it here.").font(.subheadline).foregroundStyle(Theme.secondary)
                        } else {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 14) {
                                    ForEach(followed) { show in
                                        NavigationLink { ShowView(show: show) } label: {
                                            VStack(alignment: .leading, spacing: 8) {
                                                ShowCover(show: show).frame(width: 120)
                                                Text(show.title).font(.caption.weight(.semibold)).foregroundStyle(Theme.ink).lineLimit(1)
                                            }.frame(width: 120)
                                        }.buttonStyle(.plain)
                                    }
                                }
                            }
                        }
                    }
                    NavigationLink { QueueView() } label: {
                        HStack {
                            Label("Up next", systemImage: "list.bullet").font(.subheadline.weight(.semibold))
                            Spacer()
                            Text("\(player.queuedStories.count)").font(.subheadline).foregroundStyle(Theme.secondary)
                            Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
                        }.foregroundStyle(Theme.ink).card(padding: 16, radius: OpenAIKit.Radius.card)
                    }.buttonStyle(.plain)
                    VStack(alignment: .leading, spacing: 8) {
                        Picker("Collection", selection: $selection) { Text("Saved").tag(0); Text("In progress").tag(1); Text("Played").tag(2) }
                            .pickerStyle(.segmented)
                        if items.isEmpty {
                            ContentUnavailableView(selection == 0 ? "Nothing saved yet" : selection == 1 ? "Nothing in progress" : "Nothing played yet",
                                                   systemImage: selection == 0 ? "bookmark" : selection == 1 ? "headphones" : "checkmark.circle",
                                                   description: Text(selection == 0 ? "Tap the bookmark on any episode to save it." : selection == 1 ? "Episodes you start will appear here." : "Finished episodes will appear here."))
                        }
                        ForEach(items) { EpisodeRow(story: $0) }
                    }
                }
                .padding(.horizontal, 20).padding(.bottom, 24)
            }
            .background(Theme.canvas)
            .navigationTitle("Library")
        }
    }
}
