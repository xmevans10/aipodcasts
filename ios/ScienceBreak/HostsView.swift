import SwiftUI

/// The people (well, personas) behind the shows.
struct HostsView: View {
    @EnvironmentObject var library: Library
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text("Four hosts, four beats. Each one fronts a show and never leaves their evidence behind.")
                        .font(.subheadline).foregroundStyle(Theme.secondary)
                    ForEach(Show.all) { show in
                        NavigationLink { HostView(show: show) } label: { HostCard(show: show) }.buttonStyle(.plain)
                    }
                    Label("Hosts are fictional AI presenters with synthetic voices. They present the research; they don't conduct it.", systemImage: "info.circle")
                        .font(.caption).foregroundStyle(Theme.secondary).padding(.top, 4)
                }
                .padding(.horizontal, 20).padding(.bottom, 24)
            }
            .background(Theme.canvas)
            .navigationTitle("Hosts")
        }
    }
}

private struct HostCard: View {
    @EnvironmentObject var library: Library
    var show: Show
    var body: some View {
        HStack(spacing: 16) {
            HostAvatar(host: show.host, size: 68)
            VStack(alignment: .leading, spacing: 4) {
                Text(show.host.name).font(.headline).foregroundStyle(Theme.ink)
                Text(show.host.niche).font(.caption).foregroundStyle(Theme.secondary)
                Text(show.host.personality).font(.subheadline).foregroundStyle(Theme.ink).lineLimit(2).multilineTextAlignment(.leading)
                HStack(spacing: 6) {
                    Image(systemName: show.symbol).font(.caption2)
                    Text(show.title).font(.caption.weight(.medium))
                }.foregroundStyle(Theme.secondary).padding(.top, 2)
            }
            Spacer(minLength: 0)
            Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
        }
        .card()
    }
}

struct HostView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    var show: Show
    private var episodes: [Story] { library.episodes(of: show) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 26) {
                VStack(spacing: 14) {
                    HostAvatar(host: show.host, size: 132)
                    VStack(spacing: 6) {
                        Text(show.host.name).font(Theme.display).accessibilityAddTraits(.isHeader)
                        Text(show.host.niche.uppercased()).font(.caption2.weight(.semibold)).tracking(0.8).foregroundStyle(Theme.secondary)
                    }
                    Text(show.host.personality).font(.body).foregroundStyle(Theme.ink).multilineTextAlignment(.center)
                    if let latest = episodes.first {
                        Button { player.story?.id == latest.id ? player.toggle() : player.play(latest) } label: {
                            Label(player.story?.id == latest.id && player.playing ? "Pause" : "Listen to \(show.host.name.components(separatedBy: " ")[0])",
                                  systemImage: player.story?.id == latest.id && player.playing ? "pause.fill" : "play.fill")
                        }.buttonStyle(PrimaryButtonStyle())
                    }
                }
                .frame(maxWidth: .infinity)

                NavigationLink { ShowView(show: show) } label: {
                    HStack(spacing: 14) {
                        ShowCover(show: show).frame(width: 64)
                        VStack(alignment: .leading, spacing: 3) {
                            Text("THEIR SHOW").font(.caption2.weight(.semibold)).tracking(0.6).foregroundStyle(Theme.secondary)
                            Text(show.title).font(.headline).foregroundStyle(Theme.ink)
                            Text(show.tagline).font(.caption).foregroundStyle(Theme.secondary).lineLimit(2).multilineTextAlignment(.leading)
                        }
                        Spacer(minLength: 0)
                        Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
                    }.card()
                }.buttonStyle(.plain)

                if !episodes.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        SectionHeader(title: "Episodes")
                        ForEach(Array(episodes.enumerated()), id: \.element.id) { index, story in
                            EpisodeRow(story: story, showsShow: false)
                            if index < episodes.count - 1 { Divider().overlay(Theme.hairline) }
                        }
                    }
                }

                VStack(alignment: .leading, spacing: 12) {
                    SectionHeader(title: "How \(show.host.name.components(separatedBy: " ")[0]) works")
                    detail("theatermasks", "A written character", "\(show.host.name) is an original fictional presenter. The name, interests and delivery are ours; no real researcher is portrayed.")
                    detail("waveform", "A licensed voice", "Episodes are narrated with a synthetic ElevenLabs voice, directed line by line for pace and emotion.")
                    detail("checkmark.seal", "The same evidence rules", "Hosts shape the delivery, never the findings. Every claim is checked against the source paper before an episode is approved.")
                }.card()
            }
            .padding(.horizontal, 20).padding(.top, 8).padding(.bottom, 28)
        }
        .background(Theme.canvas)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func detail(_ symbol: String, _ title: String, _ body: String) -> some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: symbol).font(.footnote.weight(.semibold)).foregroundStyle(Theme.ink)
                .frame(width: 30, height: 30).background(Theme.subtle, in: Circle())
            VStack(alignment: .leading, spacing: 3) {
                Text(title).font(.subheadline.weight(.semibold))
                Text(body).font(.caption).foregroundStyle(Theme.secondary).lineSpacing(2)
            }
        }
    }
}
