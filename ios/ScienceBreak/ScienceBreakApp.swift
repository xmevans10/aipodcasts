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
                .tint(ScienceBreak.ink).preferredColorScheme(.light)
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
            TodayView().tag(0).tabItem { Label("Today", systemImage: "sun.max") }
            ExploreView().tag(1).tabItem { Label("Discover", systemImage: "circle.grid.2x2") }
            HostsView().tag(2).tabItem { Label("Your hosts", systemImage: "waveform") }
            LibraryView().tag(3).tabItem { Label("Library", systemImage: "books.vertical") }
        }
        .safeAreaInset(edge: .bottom) {
            if let story = player.story {
                HStack(spacing: 12) {
                    Button { showPlayer = true } label: {
                        HStack(spacing: 12) {
                            HostAvatar(host: story.host, size: 36)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(story.title).font(.caption.weight(.semibold)).lineLimit(1)
                                Text(player.isPreview ? "DEVICE VOICE PREVIEW" : "\(story.host.name) · Science Break").font(.system(size: 8, weight: .medium, design: .monospaced))
                            }
                        }.foregroundStyle(ScienceBreak.paper)
                    }
                    Spacer(minLength: 0)
                    Button { player.toggle() } label: { Image(systemName: player.playing ? "pause.fill" : "play.fill").frame(width: 44, height: 44) }
                        .foregroundStyle(ScienceBreak.acid).accessibilityLabel(player.playing ? "Pause" : "Play")
                }.padding(.horizontal, 15).padding(.vertical, 7).background(ScienceBreak.ink, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.panel)).padding(.horizontal, 12).padding(.bottom, 5)
            }
        }
        .onChange(of: scenePhase) { _, phase in if phase != .active { player.checkpoint() } }
        .onChange(of: library.stories) { _, stories in player.restore(stories) }
        .sheet(isPresented: $showPlayer) { PlayerView() }
        .fullScreenCover(isPresented: Binding(get: { !onboarded }, set: { onboarded = !$0 })) { WelcomeView() }
        .task {
            #if DEBUG
            let args = ProcessInfo.processInfo.arguments
            if args.contains("--hosts") { tab = 2 }
            if args.contains("--discover") { tab = 1 }
            if args.contains("--library") { library.toggle(Story.demos[0]); tab = 3 }
            if args.contains("--player") { player.story = Story.demos[0]; showPlayer = true }
            #endif
            player.onStarted = { library.heard($0) }
            player.restore(library.stories)
            await library.refresh()
            player.restore(library.stories)
        }
    }
}
struct TodayView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @State private var settings = false
    var edition: [Story] { library.stories.filter { $0.hostID == library.hostID } + library.stories.filter { $0.hostID != library.hostID } }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 25) {
                    HStack(alignment: .center) {
                        Text("Science\nBreak").font(.system(size: 43, weight: .bold, design: .serif)).tracking(-3)
                        Circle().fill(ScienceBreak.ink).frame(width: 8, height: 8).offset(x: -6, y: 10)
                        Spacer()
                        Text("A LITTLE MORE CURIOUS.").font(.system(size: 8, weight: .semibold, design: .monospaced)).tracking(1)
                        Button { settings = true } label: { Image(systemName: "slider.horizontal.3").frame(width: 44, height: 44) }.accessibilityLabel("Settings")
                    }
                    HStack { Eyebrow(text: Date.now.formatted(.dateTime.weekday(.wide).month(.abbreviated).day()).uppercased()); Spacer(); Eyebrow(text: "YOUR DAILY ORBIT") }
                    Text("Big ideas.\nEasy listening.").font(.system(size: 43, weight: .regular, design: .serif)).tracking(-1.8).lineSpacing(-1)
                    if let story = edition.first {
                        VStack(alignment: .leading, spacing: 0) {
                            NavigationLink { ArticleView(story: story) } label: {
                                OrbitalArt(hue: story.host.hue).frame(height: 219).overlay(alignment: .bottomLeading) {
                                    Text(story.isDemo ? "THE DEMO EDITION" : "TODAY’S BIG IDEA").font(.system(size: 9, weight: .bold, design: .monospaced)).tracking(1.5).padding(10).background(ScienceBreak.acid, in: Capsule()).padding(16)
                                }
                            }
                            VStack(alignment: .leading, spacing: 13) {
                                Eyebrow(text: "\(story.topic)  /  \(story.minutes) MIN LISTEN")
                                NavigationLink { ArticleView(story: story) } label: { Text(story.title).font(.system(size: 28, design: .serif)).tracking(-0.6).multilineTextAlignment(.leading) }.buttonStyle(.plain)
                                Text(story.dek).font(.subheadline).foregroundStyle(ScienceBreak.muted)
                                HStack {
                                    HostAvatar(host: story.host, size: 30)
                                    Text("with \(story.host.name)").font(.caption)
                                    Spacer()
                                    Button { player.play(story) } label: { Label("Listen", systemImage: "play.fill") }.buttonStyle(CapsuleButton())
                                }.padding(.top, 3)
                            }.padding(20)
                        }.background(.white.opacity(0.72), in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.hero)).clipShape(RoundedRectangle(cornerRadius: OpenAIKit.Radius.hero))
                    }
                    Button { player.playEdition(edition) } label: { Label("Play this edition · \(edition.reduce(0) { $0 + $1.minutes }) min", systemImage: "text.line.first.and.arrowtriangle.forward") }.buttonStyle(CapsuleButton()).disabled(edition.isEmpty)
                    HStack { Text("A little further down the rabbit hole").font(.system(size: 22, design: .serif)); Spacer(); Image(systemName: "arrow.down.right") }
                    ForEach(edition.dropFirst()) { story in
                        NavigationLink { ArticleView(story: story) } label: { StoryRow(story: story) }.buttonStyle(.plain)
                    }
                    if library.stories.isEmpty { ContentUnavailableView("A quiet orbit", systemImage: "sparkles", description: Text("New stories will appear after editorial review.")) }
                    if let error = library.error { Text(error).font(.caption).foregroundStyle(.red) }
                    Text("Curiosity, with receipts. Every story links back to its sources.").font(.caption).foregroundStyle(ScienceBreak.muted).padding(.bottom, 20)
                }.padding(.horizontal, 22)
            }.background(ScienceBreak.paper).toolbar(.hidden, for: .navigationBar).refreshable { await library.refresh() }
                .sheet(isPresented: $settings) { SettingsView() }
        }
    }
}
struct ExploreView: View {
    @EnvironmentObject var library: Library
    @State private var search = ""
    @State private var topic = "All"
    private let topics = ["All", "SPACE", "NATURE", "MIND", "EARTH"]
    var filtered: [Story] { library.stories.filter { (topic == "All" || $0.topic == topic) && (search.isEmpty || ($0.title + $0.dek + $0.body).localizedCaseInsensitiveContains(search)) } }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    Eyebrow(text: "FOLLOW YOUR CURIOSITY")
                    Text("There’s a world\nin here.").font(.system(size: 40, design: .serif)).tracking(-1)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack { ForEach(topics, id: \.self) { t in Button(t.capitalized) { topic = t }.font(.caption.weight(.semibold)).padding(.horizontal, 17).padding(.vertical, 13).background(topic == t ? ScienceBreak.ink : .white, in: Capsule()).foregroundStyle(topic == t ? ScienceBreak.paper : ScienceBreak.ink) } }
                    }
                    ForEach(filtered) { story in NavigationLink { ArticleView(story: story) } label: { StoryRow(story: story) }.buttonStyle(.plain) }
                    if filtered.isEmpty { ContentUnavailableView.search(text: search) }
                }.padding(22)
            }.background(ScienceBreak.paper).navigationTitle("Discover").navigationBarTitleDisplayMode(.inline).searchable(text: $search, prompt: "Space, brains, wild ideas…")
        }
    }
}
struct HostsView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    Eyebrow(text: "GOOD COMPANY FOR GREAT IDEAS")
                    Text("Find your\nkind of curious.").font(.system(size: 40, design: .serif)).tracking(-1)
                    Text("Four perspectives. One commitment to the facts. Your host shapes the delivery, never the evidence.").font(.subheadline).foregroundStyle(ScienceBreak.muted)
                    ForEach(Host.all) { host in
                        VStack(alignment: .leading, spacing: 17) {
                            HStack { HostAvatar(host: host, size: 65); Spacer(); if library.hostID == host.id { Label("Your host", systemImage: "checkmark").font(.caption).padding(9).background(ScienceBreak.acid, in: Capsule()) } }
                            HStack(alignment: .firstTextBaseline) { Text(host.name).font(.system(size: 30, design: .serif)); Text(host.niche).font(.caption).foregroundStyle(ScienceBreak.muted) }
                            Text(host.personality).font(.subheadline)
                            HStack {
                                Button { library.hostID = host.id } label: { Text(library.hostID == host.id ? "Selected" : "Choose \(host.name)") }.buttonStyle(CapsuleButton())
                                Spacer()
                                Button { if let story = library.stories.first(where: { $0.hostID == host.id }) { player.play(story, host: host) } } label: { Label("Preview", systemImage: "play.circle") }.font(.subheadline)
                            }
                        }.padding(22).background(.white.opacity(0.75), in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.hero))
                    }
                    Text("Fictional AI hosts. Demo previews use device voices; production uses licensed ElevenLabs voices. Stories use their assigned niche host.").font(.caption).foregroundStyle(ScienceBreak.muted)
                }.padding(22)
            }.background(ScienceBreak.paper).navigationTitle("Your hosts").navigationBarTitleDisplayMode(.inline)
        }
    }
}
struct LibraryView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @State private var selection = 0
    var items: [Story] { library.stories.filter {
        switch selection {
        case 0: return library.saved.contains($0.id)
        case 1: return library.history.contains($0.id) && !player.listening.completed.contains($0.id)
        default: return player.listening.completed.contains($0.id)
        }
    } }
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    Text("Keep a little\nwonder.").font(.system(size: 40, design: .serif)).tracking(-1)
                    NavigationLink { QueueView() } label: {
                        HStack { Label("Your listening queue", systemImage: "text.line.first.and.arrowtriangle.forward"); Spacer(); Text("\(player.queuedStories.count)"); Image(systemName: "chevron.right") }
                            .font(.subheadline.weight(.semibold)).padding(20).background(ScienceBreak.acid, in: RoundedRectangle(cornerRadius: 18))
                    }.buttonStyle(.plain)
                    Picker("Collection", selection: $selection) { Text("Saved").tag(0); Text("Listening").tag(1); Text("Finished").tag(2) }.pickerStyle(.segmented)
                    if items.isEmpty { ContentUnavailableView(selection == 0 ? "Your next rabbit hole" : selection == 1 ? "Your listening starts here" : "More curious by the day", systemImage: selection == 0 ? "bookmark" : "headphones", description: Text(selection == 0 ? "Save a story to come back to it." : selection == 1 ? "Start a story from Today or Discover." : "Stories you finish will appear here.")) }
                    ForEach(items) { story in
                        VStack(alignment: .leading, spacing: 8) {
                            NavigationLink { ArticleView(story: story) } label: { StoryRow(story: story) }.buttonStyle(.plain)
                            if selection == 1 {
                                Button { player.play(story) } label: {
                                    Label((player.listening.positions[story.id] ?? 0) > 0 ? "Continue listening" : "Listen again", systemImage: "play.fill")
                                }.font(.caption.weight(.semibold))
                            }
                        }
                    }
                }.padding(22)
            }.background(ScienceBreak.paper).navigationTitle("Library").navigationBarTitleDisplayMode(.inline)
        }
    }
}
