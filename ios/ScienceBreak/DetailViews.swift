import SwiftUI
import StoreKit

struct EpisodeView: View {
    let story: Story
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    private var isCurrent: Bool { player.story?.id == story.id }
    private var queued: Bool { player.listening.queue.contains(story.id) }

    @State private var headerPassed = false
    private let fade: CGFloat = 72

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                header

                EpisodeMeta(story: story).padding(.top, -4)

                HStack(spacing: 10) {
                    Button { isCurrent ? player.toggle() : player.play(story) } label: {
                        Label(isCurrent && player.playing ? "Pause" : player.progress(of: story) > 0 && player.progress(of: story) < 1 ? "Resume" : "Play",
                              systemImage: isCurrent && player.playing ? "pause.fill" : "play.fill")
                    }.buttonStyle(PrimaryButtonStyle(show: story.show))
                    Spacer()
                    iconButton(queued ? "text.badge.checkmark" : "text.badge.plus", label: queued ? "In your queue" : "Add to queue") { player.enqueue(story) }
                        .disabled(queued || isCurrent)
                    iconButton(library.saved.contains(story.id) ? "bookmark.fill" : "bookmark", label: library.saved.contains(story.id) ? "Unsave" : "Save") { library.toggle(story) }
                    ShareLink(item: "\(story.title) — \(story.show.title) on Sound Science") {
                        Image(systemName: "square.and.arrow.up").modifier(IconCircle())
                    }.accessibilityLabel("Share")
                }

                if story.audioURL == nil {
                    Label("Device voice sample. This preview is narrated on your device.", systemImage: "waveform")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }

                if let transcript = Episodes.transcript(for: story.id) {
                    NavigationLink { TranscriptView(story: story, paragraphs: transcript) } label: {
                        HStack(spacing: 14) {
                            Image(systemName: "text.quote").font(.title3).foregroundStyle(Theme.ink).frame(width: 40, height: 40).background(Theme.subtle, in: Circle())
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Read along").font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
                                Text("Follow the transcript as it plays").font(.caption).foregroundStyle(Theme.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
                        }.card(padding: 14, radius: OpenAIKit.Radius.card)
                    }.buttonStyle(.plain)
                }

                VStack(alignment: .leading, spacing: 10) {
                    Label("About this episode", systemImage: "info.circle").font(.subheadline.weight(.semibold))
                    Text(story.caveat).font(.subheadline).foregroundStyle(Theme.secondary).lineSpacing(3)
                }
                .padding(16).frame(maxWidth: .infinity, alignment: .leading)
                .background(Theme.subtle, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))

                VStack(alignment: .leading, spacing: 12) {
                    SectionHeader(title: "Sources")
                    ForEach(Array(story.sources.enumerated()), id: \.element.url) { index, source in
                        HStack(alignment: .top, spacing: 12) {
                            Text("\(index + 1)").font(.caption.weight(.semibold).monospacedDigit()).foregroundStyle(Theme.secondary)
                                .frame(width: 22, height: 22).background(Theme.subtle, in: Circle())
                            VStack(alignment: .leading, spacing: 4) {
                                if let url = URL(string: source.url), url.scheme == "https" {
                                    Link(destination: url) {
                                        HStack(alignment: .firstTextBaseline, spacing: 4) {
                                            Text(source.title).multilineTextAlignment(.leading)
                                            Image(systemName: "arrow.up.right").font(.caption2)
                                        }
                                    }.font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
                                } else {
                                    Text(source.title).font(.subheadline.weight(.semibold))
                                }
                                Text(source.attribution).font(.caption).foregroundStyle(Theme.secondary)
                                Text(source.license).font(.caption).foregroundStyle(Theme.tertiary)
                            }
                        }
                    }
                }

                VStack(alignment: .leading, spacing: 12) {
                    SectionHeader(title: "Transcript")
                    Text(story.body).font(Theme.reading(18)).foregroundStyle(Theme.ink).lineSpacing(7).textSelection(.enabled)
                }
            }
            .padding(.horizontal, 20).padding(.bottom, 28)
        }
        .background(Theme.canvas)
        .immersiveNavigationBar(show: story.show, title: story.show.title, solid: headerPassed)
    }

    /// Colour band in the show's wash behind the show chip and title, fading into the canvas.
    private var header: some View {
        VStack(alignment: .leading, spacing: 22) {
            NavigationLink { ShowView(show: story.show) } label: {
                HStack(spacing: 12) {
                    ShowCover(show: story.show).frame(width: 44)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(story.show.title).font(.subheadline.weight(.semibold)).foregroundStyle(.white)
                        Text("with \(story.host.name)").font(.caption).foregroundStyle(.white.opacity(0.8))
                    }
                    Spacer()
                    Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(.white.opacity(0.7))
                }
                .padding(10).padding(.trailing, 4)
                .background(.white.opacity(0.12), in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))
                .contentShape(Rectangle())
            }.buttonStyle(.plain)

            VStack(alignment: .leading, spacing: 10) {
                Text(story.title).font(Theme.display).foregroundStyle(.white).accessibilityAddTraits(.isHeader)
                Text(story.dek).font(.body).foregroundStyle(.white.opacity(0.85))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.top, 8)
        .modifier(HeaderScrollTracker(passed: $headerPassed))
        .padding(.bottom, fade - 22)
        .background(alignment: .bottom) {
            // Full-bleed: out past the page's side padding.
            ImmersiveHeaderBackground(show: story.show, fade: fade).padding(.horizontal, -20)
        }
    }

    private func iconButton(_ symbol: String, label: String, action: @escaping () -> Void) -> some View {
        Button(action: action) { Image(systemName: symbol).modifier(IconCircle()) }.accessibilityLabel(label)
    }
}

struct IconCircle: ViewModifier {
    func body(content: Content) -> some View {
        content.font(.body.weight(.medium)).foregroundStyle(Theme.ink)
            .frame(width: 44, height: 44).background(Theme.surface, in: Circle()).overlay(Circle().strokeBorder(Theme.hairline))
    }
}

struct PlayerView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    @Environment(\.dismiss) var dismiss
    private let soft = Color.white.opacity(0.75)

    /// Swiping a page plays that episode; selection tracks the current story.
    private var selection: Binding<Int> {
        Binding(
            get: { player.playlistIndex(of: player.story?.id) ?? 0 },
            set: { index in
                let list = player.playlist
                guard list.indices.contains(index), list[index].id != player.story?.id else { return }
                Haptics.tap()
                player.play(list[index])
            }
        )
    }

    var body: some View {
        NavigationStack {
            Group {
                if player.playlist.isEmpty {
                    Theme.canvas.ignoresSafeArea()
                } else {
                    TabView(selection: selection) {
                        ForEach(Array(player.playlist.enumerated()), id: \.element.id) { index, story in
                            page(story).tag(index)
                        }
                    }
                    .tabViewStyle(.page(indexDisplayMode: .never))
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "chevron.down").font(.body.weight(.semibold)).foregroundStyle(.white)
                            .frame(width: 34, height: 34).background(.white.opacity(0.14), in: Circle())
                            .frame(minWidth: 44, minHeight: 44)
                    }.accessibilityLabel("Close")
                }
            }
            .toolbarBackground(.hidden, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
            .animation(.easeInOut(duration: 0.4), value: player.story?.show.id)
        }
    }

    private func page(_ story: Story) -> some View {
        let active = player.story?.id == story.id
        let preview = story.audioURL == nil
        let playing = active && player.playing
        let position = active ? player.position : (player.listening.positions[story.id] ?? 0)
        let duration = active ? player.duration : Double(story.minutes * 60)
        return ScrollView {
                    VStack(spacing: 24) {
                        ZStack {
                            CoverGlow(show: story.show, size: 300)
                            RoundedRectangle(cornerRadius: 34, style: .continuous)
                                .fill(LinearGradient(colors: [story.show.light, story.show.mid, story.show.dark],
                                                     startPoint: .topTrailing, endPoint: .bottomLeading))
                                .overlay(RoundedRectangle(cornerRadius: 34, style: .continuous).strokeBorder(.white.opacity(0.18)))
                                .shadow(color: .black.opacity(0.35), radius: 30, y: 18)
                            HostAvatar(host: story.host, size: 196)
                                .shadow(color: story.show.dark.opacity(0.35), radius: 18, y: 10)
                        }
                        .frame(maxWidth: 300).aspectRatio(1, contentMode: .fit).padding(.top, 4)
                        VStack(spacing: 8) {
                            HStack(spacing: 8) {
                                HostAvatar(host: story.host, size: 22).overlay(Circle().strokeBorder(.white.opacity(0.6)))
                                Text("\(story.show.title) · \(story.host.name)").font(.subheadline).foregroundStyle(soft)
                            }
                            Text(story.title).font(.system(size: 24, weight: .semibold, design: .serif)).foregroundStyle(.white).multilineTextAlignment(.center)
                        }
                        if !preview {
                            VStack(spacing: 4) {
                                Slider(value: Binding(get: { min(position, duration) }, set: { if active { player.seek($0) } }), in: 0...max(duration, 1))
                                    .tint(.white).accessibilityLabel("Playback position")
                                HStack { Text(clock(position)); Spacer(); Text("-" + clock(max(0, duration - position))) }
                                    .font(.caption.monospacedDigit()).foregroundStyle(soft)
                            }
                        } else {
                            Text("Device voice sample. Produced episodes use licensed ElevenLabs narration.").font(.caption).foregroundStyle(soft).multilineTextAlignment(.center)
                        }
                        HStack(spacing: 44) {
                            Button { if active { player.seek(position - 15) } } label: { Image(systemName: "gobackward.15").font(.title2) }.disabled(preview || !active).accessibilityLabel("Back 15 seconds")
                            Button { if active { player.toggle() } else { player.play(story) } } label: {
                                Image(systemName: playing ? "pause.fill" : "play.fill").font(.title).foregroundStyle(story.show.dark)
                                    .frame(width: 76, height: 76)
                                    .background(Circle().fill(.white))
                                    .shadow(color: .black.opacity(0.3), radius: 14, y: 6)
                            }.accessibilityLabel(playing ? "Pause" : "Play")
                            Button { if active { player.seek(position + 15) } } label: { Image(systemName: "goforward.15").font(.title2) }.disabled(preview || !active).accessibilityLabel("Forward 15 seconds")
                        }.foregroundStyle(.white)
                        HStack {
                            Button { if active { player.cycleRate() } } label: { Text(String(format: "%.2gx", active ? player.rate : 1)).font(.subheadline.weight(.semibold)).frame(width: 52, height: 44) }.accessibilityLabel("Playback speed")
                            Spacer()
                            Menu {
                                if player.sleepUntil != nil { Button("Cancel sleep timer") { player.cancelSleep() } }
                                Button("15 minutes") { player.sleep(minutes: 15) }; Button("30 minutes") { player.sleep(minutes: 30) }
                            } label: { Image(systemName: player.sleepUntil == nil ? "moon" : "moon.fill").foregroundStyle(.white).frame(width: 44, height: 44) }.accessibilityLabel("Sleep timer")
                            Spacer()
                            NavigationLink { QueueView() } label: {
                                Image(systemName: "list.bullet").frame(width: 44, height: 44)
                                    .overlay(alignment: .topTrailing) {
                                        if !player.queuedStories.isEmpty {
                                            Text("\(player.queuedStories.count)").font(.system(size: 10, weight: .bold)).foregroundStyle(story.show.dark)
                                                .frame(minWidth: 16, minHeight: 16).background(.white, in: Circle()).offset(x: -4, y: 4)
                                        }
                                    }
                            }.accessibilityLabel("Up next, \(player.queuedStories.count) episodes")
                            Spacer()
                            Button { library.toggle(story) } label: { Image(systemName: library.saved.contains(story.id) ? "bookmark.fill" : "bookmark").frame(width: 44, height: 44) }
                                .accessibilityLabel(library.saved.contains(story.id) ? "Unsave" : "Save")
                        }.font(.title3).foregroundStyle(.white)
                        if active, let message = player.message { Text(message).font(.caption).foregroundStyle(soft) }
                        VStack(spacing: 10) {
                            if let transcript = Episodes.transcript(for: story.id) {
                                NavigationLink { TranscriptView(story: story, paragraphs: transcript) } label: {
                                    Label("Read along", systemImage: "text.quote")
                                }.buttonStyle(OnColorSecondaryButtonStyle(fullWidth: true))
                            }
                            NavigationLink { EpisodeView(story: story) } label: { Label("Episode details & sources", systemImage: "doc.text") }
                                .buttonStyle(OnColorSecondaryButtonStyle(fullWidth: true))
                            if active, let next = player.queuedStories.first {
                                Button { player.next() } label: {
                                    HStack { Text("Up next").foregroundStyle(soft); Text(next.title).lineLimit(1); Spacer(); Image(systemName: "forward.end.fill") }
                                        .font(.subheadline).foregroundStyle(.white).padding(.top, 4)
                                }
                            }
                        }
                    }
                    .padding(.horizontal, 24).padding(.bottom, 24)
        }
        .background { PlayerBackdrop(show: story.show).ignoresSafeArea() }
    }
    func clock(_ time: Double) -> String { "\(Int(time) / 60):\(String(format: "%02d", Int(time) % 60))" }
}

struct SettingsView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    @Environment(\.dismiss) var dismiss
    @AppStorage("onboarded") var onboarded = true
    @State private var plus = false
    @State private var reset = false
    var body: some View {
        NavigationStack {
            Form {
                #if DEBUG
                Section("Membership") {
                    Button("Sound Science Plus") { plus = true }
                    Text("Preview build · All episodes are free").font(.caption).foregroundStyle(Theme.secondary)
                }
                #endif
                Section("Connected feed") {
                    TextField("HTTPS feed URL", text: $library.feedURL).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    Button(library.loading ? "Refreshing…" : "Refresh episodes") { Task { await library.refresh() } }.disabled(library.loading)
                    if let error = library.error { Text(error).foregroundStyle(.red).font(.caption) }
                }
                Section("Trust & privacy") {
                    NavigationLink("How an episode is made") { PolicyView(title: "How an episode is made", text: "We select sources with explicit reuse permission, write an original explanation, check its claims against the source, and require an editor’s approval before publishing.\n\nAI can make mistakes. Every episode includes attribution, a note on what the evidence can and can’t show, and links to the original sources. Hosts are fictional AI presenters, never the researchers themselves.\n\nThe episodes in this preview build were checked against their sources by an assistant; independent editorial approval is still pending.") }
                    NavigationLink("Privacy") { PolicyView(title: "Privacy", text: "This preview stores your saved episodes, followed shows, listening queue, playback positions, finished episodes and listening minutes on your device using UserDefaults. It contains no advertising or analytics SDKs and does not create an account.\n\nConnecting a feed sends normal network requests, including your IP address, to the server you configure. Opening source links is subject to the destination’s privacy policy. Production privacy terms must name the operating company and its data processors before launch.") }
                    Button("Delete local listening data", role: .destructive) { reset = true }
                }
                Section("Credits") {
                    Text("Host illustrations: DiceBear “Notionists” (CC0). Narration: ElevenLabs. Reading typeface: Charter.").font(.caption).foregroundStyle(Theme.secondary)
                }
                Section { Button("Show welcome again") { onboarded = false; dismiss() }; Text("Sound Science 0.1").font(.caption).foregroundStyle(Theme.secondary) }
            }
            .navigationTitle("Settings").toolbar { Button("Done") { dismiss() } }
            .sheet(isPresented: $plus) {
                #if DEBUG
                PlusView()
                #else
                EmptyView()
                #endif
            }
            .confirmationDialog("Delete saved episodes, queue and listening history?", isPresented: $reset, titleVisibility: .visible) {
                Button("Delete local data", role: .destructive) { player.clearListeningData(); library.saved = []; library.history = []; UserDefaults.standard.removeObject(forKey: "saved"); UserDefaults.standard.removeObject(forKey: "history") }
            }
        }
    }
}

struct PolicyView: View {
    var title: String
    var text: String
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text(title).font(Theme.display)
                Text(text).font(Theme.reading(18)).lineSpacing(6)
            }.padding(24)
        }.background(Theme.canvas)
    }
}

struct PlusView: View {
    @Environment(\.dismiss) var dismiss
    var body: some View {
        NavigationStack {
            VStack(spacing: 18) {
                Text("SOUND SCIENCE PLUS").font(.caption2.weight(.semibold)).tracking(0.8).foregroundStyle(Theme.secondary)
                Text("The full archive, offline.").font(Theme.display).multilineTextAlignment(.center)
                Text("Planned for launch: every past episode, downloads for offline listening, and longer listening sessions.").multilineTextAlignment(.center).foregroundStyle(Theme.secondary)
                if let ids = Bundle.main.object(forInfoDictionaryKey: "ScienceBreakSubscriptionProducts") as? String, !ids.isEmpty {
                    SubscriptionStoreView(productIDs: ids.split(separator: ",").map(String.init))
                        .storeButton(.visible, for: .restorePurchases)
                } else {
                    VStack(spacing: 6) {
                        Text("Coming after the private beta").font(.headline)
                        Text("Purchases are not enabled in this build. All episodes are free.").font(.subheadline).foregroundStyle(Theme.secondary).multilineTextAlignment(.center)
                    }.card().padding(.top, 12)
                }
                Spacer()
            }.padding(28).background(Theme.canvas).toolbar { Button("Done") { dismiss() } }
        }
    }
}
