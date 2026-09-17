import SwiftUI

@main struct ScienceBreakApp: App {
    @StateObject private var library = Library()
    @StateObject private var player = AudioPlayer()
    init() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--demo") { UserDefaults.standard.set(true, forKey: "onboarded") }
        if ProcessInfo.processInfo.arguments.contains("--onboarding") { UserDefaults.standard.set(false, forKey: "onboarded") }
        #endif
    }
    var body: some Scene {
        WindowGroup {
            RootView().environmentObject(library).environmentObject(player)
                .tint(Theme.ink).preferredColorScheme(.light)
        }
    }
}

struct RootView: View {
    @Environment(\.scenePhase) private var scenePhase
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @AppStorage("onboarded") private var onboarded = false
    @State private var showPlayer = false
    @State private var tab = 0
    var body: some View {
        TabView(selection: $tab) {
            HomeView().miniPlayerInset($showPlayer).tag(0).tabItem { Label("Home", systemImage: "house") }
            BrowseView().miniPlayerInset($showPlayer).tag(1).tabItem { Label("Browse", systemImage: "square.grid.2x2") }
            LibraryView().miniPlayerInset($showPlayer).tag(2).tabItem { Label("Library", systemImage: "books.vertical") }
        }
        .onChange(of: scenePhase) { _, phase in if phase != .active { player.checkpoint() } }
        .onChange(of: library.stories) { _, stories in player.restore(stories) }
        .sheet(isPresented: $showPlayer) { PlayerView() }
        .fullScreenCover(isPresented: Binding(get: { !onboarded }, set: { onboarded = !$0 })) { WelcomeView() }
        .task {
            #if DEBUG
            let args = ProcessInfo.processInfo.arguments
            if args.contains("--browse") { tab = 1 }
            if args.contains("--library") { library.toggle(Story.demos[0]); tab = 2 }
            if args.contains("--player") { player.story = Story.demos[0]; showPlayer = true }
            #endif
            player.onStarted = { library.heard($0) }
            player.restore(library.stories)
            await library.refresh()
            player.restore(library.stories)
        }
    }
}

struct MiniPlayerInset: ViewModifier {
    @EnvironmentObject var player: AudioPlayer
    @Binding var showPlayer: Bool
    func body(content: Content) -> some View {
        content.safeAreaInset(edge: .bottom) {
            if let story = player.story {
                HStack(spacing: 10) {
                    Button { showPlayer = true } label: {
                        HStack(spacing: 12) {
                            ShowCover(show: story.show).frame(width: 42)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(story.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).lineLimit(1)
                                Text(player.isPreview ? "\(story.show.title) · Device voice sample" : story.show.title)
                                    .font(.caption).foregroundStyle(Theme.secondary).lineLimit(1)
                            }
                            Spacer(minLength: 0)
                        }.contentShape(Rectangle())
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Now playing: \(story.title). Opens player.")
                    Button { player.toggle() } label: {
                        Image(systemName: player.playing ? "pause.fill" : "play.fill").font(.title3).foregroundStyle(Theme.ink).frame(width: 44, height: 44)
                    }.accessibilityLabel(player.playing ? "Pause" : "Play")
                }
                .padding(.leading, 8).padding(.trailing, 4).padding(.vertical, 7)
                .background(Theme.surface)
                .overlay(alignment: .bottom) {
                    if !player.isPreview {
                        GeometryReader { g in
                            Rectangle().fill(Theme.ink).frame(width: g.size.width * min(1, player.position / max(player.duration, 1)), height: 2)
                        }.frame(height: 2)
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(Theme.hairline))
                .shadow(color: .black.opacity(0.08), radius: 14, y: 6)
                .padding(.horizontal, 10).padding(.bottom, 6)
            }
        }
    }
}

extension View {
    func miniPlayerInset(_ showPlayer: Binding<Bool>) -> some View { modifier(MiniPlayerInset(showPlayer: showPlayer)) }
}
