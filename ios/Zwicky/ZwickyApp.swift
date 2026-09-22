import SwiftUI

@main struct ZwickyApp: App {
    @StateObject private var library = Library()
    @StateObject private var player = AudioPlayer()
    init() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--demo") { UserDefaults.standard.set(true, forKey: "onboarded") }
        if ProcessInfo.processInfo.arguments.contains("--onboarding") { UserDefaults.standard.set(false, forKey: "onboarded") }
        if ProcessInfo.processInfo.arguments.contains("--newepisodes") { UserDefaults.standard.set("2000-01-01", forKey: "lastSeenPublished") }
        #endif
        // Frosted tab bar: content scrolls softly beneath it, separated by a warm hairline.
        let tabBar = UITabBarAppearance()
        tabBar.configureWithTransparentBackground()
        tabBar.backgroundEffect = UIBlurEffect(style: .systemUltraThinMaterialLight)
        tabBar.backgroundColor = UIColor(red: 0.98, green: 0.976, blue: 0.965, alpha: 0.6)
        tabBar.shadowColor = UIColor(red: 0.227, green: 0.18, blue: 0.122, alpha: 0.08)
        UITabBar.appearance().standardAppearance = tabBar
        UITabBar.appearance().scrollEdgeAppearance = tabBar
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
    @State private var tab = 0
    @State private var showNewEpisodes = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Namespace private var playerZoom
    /// Each tab has its own mini player, so the zoom source ID is per tab.
    private func inset(_ tag: Int) -> MiniPlayerInset {
        MiniPlayerInset(zoom: reduceMotion ? nil : playerZoom, tabTag: tag)
    }
    var body: some View {
        TabView(selection: $tab) {
            HomeView().modifier(inset(0)).tag(0).badge(library.unseenNewCount).tabItem { Label("Home", systemImage: "house") }
            BrowseView().modifier(inset(1)).tag(1).tabItem { Label("Browse", systemImage: "square.grid.2x2") }
            HostsView().modifier(inset(2)).tag(2).tabItem { Label("Hosts", systemImage: "person.2") }
            LibraryView().modifier(inset(3)).tag(3).tabItem { Label("Library", systemImage: "books.vertical") }
            YouView().modifier(inset(4)).tag(4).tabItem { Label("You", systemImage: "chart.bar") }
        }
        .onChange(of: scenePhase) { _, phase in if phase != .active { player.checkpoint() } }
        .onChange(of: library.stories) { _, stories in player.restore(stories) }
        .onChange(of: library.shouldAnnounceNew) { _, show in if show { showNewEpisodes = true } }
        .onChange(of: player.listening.queue) { _, _ in library.pin(player.queuedStories + [player.story].compactMap { $0 }) }
        .onChange(of: player.story?.id) { _, _ in if let story = player.story { library.pin([story]) } }
        .sheet(isPresented: $player.isPlayerPresented) {
            PlayerView().playerZoomDestination(id: MiniPlayerInset.zoomID(tab: tab), in: reduceMotion ? nil : playerZoom)
        }
        .sheet(isPresented: $showNewEpisodes) { NewEpisodesSheet().onDisappear { library.markNewSeen() } }
        .fullScreenCover(isPresented: Binding(get: { !onboarded }, set: { onboarded = !$0 })) { WelcomeView() }
        .task {
            #if DEBUG
            let args = ProcessInfo.processInfo.arguments
            if args.contains("--browse") { tab = 1 }
            if args.contains("--hosts") { tab = 2 }
            if args.contains("--library") { library.toggle(Story.demos[0]); tab = 3 }
            if args.contains("--you") { tab = 4 }
            if args.contains("--player") { player.story = Story.demos[0]; player.isPlayerPresented = true }
            #endif
            player.onStarted = { library.heard($0) }
            player.restore(library.stories)
            await library.refresh()
            player.restore(library.stories)
            library.pin(player.queuedStories + [player.story].compactMap { $0 })
            if library.shouldAnnounceNew { showNewEpisodes = true }
        }
    }
}

struct MiniPlayerInset: ViewModifier {
    @EnvironmentObject var player: AudioPlayer
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    /// Namespace for the iOS 18 zoom into the player; nil disables it.
    var zoom: Namespace.ID? = nil
    var tabTag: Int = 0

    static func zoomID(tab: Int) -> String { "mini-player-cover-\(tab)" }

    func body(content: Content) -> some View {
        content.safeAreaInset(edge: .bottom) {
            ZStack {
                if let story = player.story { bar(story).transition(appearTransition) }
            }
            .animation(Motion.standard(reduceMotion: reduceMotion), value: player.story == nil)
        }
    }

    private var appearTransition: AnyTransition {
        reduceMotion ? .opacity : .move(edge: .bottom).combined(with: .opacity)
    }

    private var fraction: Double { min(1, player.position / max(player.duration, 1)) }

    private func bar(_ story: Story) -> some View {
        HStack(spacing: 10) {
            Button { player.isPlayerPresented = true } label: {
                HStack(spacing: 12) {
                    ShowCover(show: story.show).frame(width: 42)
                        .playerZoomSource(id: Self.zoomID(tab: tabTag), in: zoom)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(story.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink).lineLimit(1)
                        Text(player.isPreview ? "\(story.show.title) · Device voice sample" : story.show.title)
                            .font(.caption).foregroundStyle(Theme.secondary).lineLimit(1)
                    }
                    Spacer(minLength: 0)
                }.contentShape(Rectangle())
            }
            .buttonStyle(PressableStyle(scale: 0.98))
            .accessibilityLabel("Now playing: \(story.title). Opens player.")
            Button { Haptics.tap(); player.toggle() } label: {
                Image(systemName: player.playing ? "pause.fill" : "play.fill").font(.title3).foregroundStyle(Theme.ink)
                    .contentTransition(reduceMotion ? .identity : .symbolEffect(.replace))
                    .frame(width: 44, height: 44)
            }
            .buttonStyle(.pressable)
            .animation(Motion.standard(reduceMotion: reduceMotion), value: player.playing)
            .accessibilityLabel(player.playing ? "Pause" : "Play")
        }
        .padding(.leading, 8).padding(.trailing, 4).padding(.vertical, 7)
        .background(Theme.surface)
        .overlay(alignment: .bottom) {
            if !player.isPreview {
                GeometryReader { g in
                    Rectangle().fill(story.show.mid).frame(width: g.size.width * fraction, height: 2)
                        .animation(.easeOut(duration: 0.25), value: fraction)
                }.frame(height: 2)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous).strokeBorder(Theme.hairline))
        .shadow(color: .black.opacity(0.08), radius: 14, y: 6)
        .padding(.horizontal, 10).padding(.bottom, 6)
    }
}
