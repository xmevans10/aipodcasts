import SwiftUI
import StoreKit

struct ArticleView: View {
    let story: Story
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                OrbitalArt(hue: story.host.hue).frame(height: 270).clipShape(RoundedRectangle(cornerRadius: OpenAIKit.Radius.hero))
                Eyebrow(text: "\(story.topic) · \(story.minutes) MIN · \(story.isDemo ? "DEMO SCRIPT" : "AI-ASSISTED ARTICLE")")
                Text(story.title).font(.system(size: 38, design: .serif)).tracking(-1)
                Text(story.dek).font(.title3).foregroundStyle(ScienceBreak.muted)
                HStack {
                    Button { player.play(story) } label: { Label("Listen with \(story.host.name)", systemImage: "play.fill") }.buttonStyle(CapsuleButton())
                    Spacer()
                    Button { library.toggle(story) } label: { Image(systemName: library.saved.contains(story.id) ? "bookmark.fill" : "bookmark").frame(width: 44, height: 44) }.accessibilityLabel(library.saved.contains(story.id) ? "Unsave story" : "Save story")
                }
                Button { player.enqueue(story) } label: {
                    Label(player.listening.queue.contains(story.id) ? "Added to queue" : "Add to queue", systemImage: "text.badge.plus")
                }.font(.subheadline.weight(.semibold)).disabled(player.listening.queue.contains(story.id) || player.story?.id == story.id)
                Text(story.body).font(.system(size: 19, design: .serif)).lineSpacing(9).textSelection(.enabled)
                VStack(alignment: .leading, spacing: 12) {
                    Eyebrow(text: "THE SCIENCE, IN CONTEXT")
                    Text(story.caveat).font(.subheadline).lineSpacing(4)
                }.padding(20).background(ScienceBreak.acid.opacity(0.45), in: RoundedRectangle(cornerRadius: 18))
                Text("Follow the evidence.").font(.system(size: 28, design: .serif))
                ForEach(story.sources, id: \.url) { source in
                    VStack(alignment: .leading, spacing: 7) {
                        if let url = URL(string: source.url), url.scheme == "https" { Link(destination: url) { Label(source.title, systemImage: "arrow.up.right") }.font(.headline) }
                        Text(source.attribution).font(.caption)
                        Text(source.license).font(.caption).foregroundStyle(ScienceBreak.muted)
                    }.padding(.vertical, 6)
                }
                Text(story.isDemo ? "An original demonstration, with background links. Not current science news or a journal summary." : "Adapted with AI assistance and narrated by a synthetic voice. See the note below on review status.").font(.caption).foregroundStyle(ScienceBreak.muted)
                ShareLink(item: story.title + " — Explore the science with Sound Science.") { Label("Share this idea", systemImage: "square.and.arrow.up") }.buttonStyle(CapsuleButton())
            }.padding(22)
        }.background(ScienceBreak.paper).navigationBarTitleDisplayMode(.inline)
    }
}
struct PlayerView: View {
    @EnvironmentObject var player: AudioPlayer
    @EnvironmentObject var library: Library
    @Environment(\.dismiss) var dismiss
    var body: some View {
        NavigationStack {
            ScrollView {
                if let story = player.story {
                    VStack(spacing: 25) {
                        Eyebrow(text: player.isPreview ? "DEVICE VOICE PREVIEW" : "IN YOUR ORBIT")
                        OrbitalArt(hue: story.host.hue).frame(height: 300).clipShape(RoundedRectangle(cornerRadius: 30))
                        Text(story.title).font(.system(size: 32, design: .serif)).multilineTextAlignment(.center)
                        Label("\(story.host.name) · \(story.host.niche)", systemImage: story.host.symbol).font(.subheadline).foregroundStyle(ScienceBreak.muted)
                        if let transcript = Episodes.transcript(for: story.id) {
                            NavigationLink { TranscriptView(story: story, paragraphs: transcript) } label: {
                                Label("Read along", systemImage: "text.quote").font(.subheadline.weight(.semibold)).padding(.horizontal, 18).frame(height: 40).background(ScienceBreak.acid, in: Capsule())
                            }.foregroundStyle(ScienceBreak.ink)
                        }
                        if !player.isPreview {
                            Slider(value: Binding(get: { min(player.position, player.duration) }, set: { player.seek($0) }), in: 0...max(player.duration, 1)).accessibilityLabel("Playback position")
                            HStack { Text(clock(player.position)); Spacer(); Text(clock(player.duration)) }.font(.caption.monospacedDigit())
                        } else { Text("Sample narration from your device. ElevenLabs voices become available with a connected production feed.").font(.caption).foregroundStyle(ScienceBreak.muted).multilineTextAlignment(.center) }
                        HStack(spacing: 34) {
                            Button { player.seek(player.position - 15) } label: { Image(systemName: "gobackward.15").font(.title) }.disabled(player.isPreview).accessibilityLabel("Back 15 seconds")
                            Button { player.toggle() } label: { Image(systemName: player.playing ? "pause.fill" : "play.fill").font(.title).frame(width: 82, height: 82).background(ScienceBreak.ink, in: Circle()).foregroundStyle(ScienceBreak.acid) }.accessibilityLabel(player.playing ? "Pause" : "Play")
                            Button { player.seek(player.position + 15) } label: { Image(systemName: "goforward.15").font(.title) }.disabled(player.isPreview).accessibilityLabel("Forward 15 seconds")
                        }
                        HStack {
                            Button { player.cycleRate() } label: { Text(String(format: "%.2gx", player.rate)).frame(width: 60, height: 44) }.accessibilityLabel("Playback speed")
                            Spacer()
                            Menu { if player.sleepUntil != nil { Button("Cancel sleep timer") { player.cancelSleep() } }; Button("15 minutes") { player.sleep(minutes: 15) }; Button("30 minutes") { player.sleep(minutes: 30) } } label: { Label(player.sleepUntil == nil ? "Sleep" : "Timer on", systemImage: "moon").frame(height: 44) }
                            Spacer()
                            Button { library.toggle(story) } label: { Image(systemName: library.saved.contains(story.id) ? "bookmark.fill" : "bookmark").frame(width: 44, height: 44) }.accessibilityLabel("Save or unsave")
                        }
                        if let message = player.message { Text(message).font(.caption).foregroundStyle(ScienceBreak.muted) }
                        HStack {
                            NavigationLink { QueueView() } label: { Label("Queue · \(player.queuedStories.count)", systemImage: "list.bullet") }
                            Spacer()
                            Button { player.next() } label: { Label("Next", systemImage: "forward.end.fill") }.disabled(player.queuedStories.isEmpty)
                        }.font(.subheadline.weight(.semibold))
                        NavigationLink("Read the story & sources") { ArticleView(story: story) }.font(.subheadline.weight(.semibold))
                    }.padding(25)
                }
            }.background(ScienceBreak.paper).toolbar { ToolbarItem(placement: .topBarLeading) { Button("Close", systemImage: "chevron.down") { dismiss() } } }
        }
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
                Section("Your little daily ritual") {
                    Button("Explore Sound Science Plus") { plus = true }
                    Text("Demo edition · Original sample stories").font(.caption)
                }
                Section("Connected edition") {
                    TextField("HTTPS feed URL", text: $library.feedURL).keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                    Button(library.loading ? "Refreshing…" : "Refresh stories") { Task { await library.refresh() } }.disabled(library.loading)
                    if let error = library.error { Text(error).foregroundStyle(.red).font(.caption) }
                }
                Section("Trust & privacy") {
                    NavigationLink("How Sound Science makes a story") { PolicyView(title: "Curiosity, with receipts.", text: "We select sources with explicit reuse permission, create an original explanation, check its claims against the source, and require an editor’s approval before publishing.\n\nAI can make mistakes. Every published story includes attribution, an uncertainty note and links to the original evidence. Hosts are fictional synthetic narrators, never the researchers themselves.\n\nThe current app contains original educational demo scripts. Device voices stand in for licensed production narration.") }
                    NavigationLink("Privacy") { PolicyView(title: "Your curiosity is yours.", text: "This demo stores your saved story IDs, listening queue, playback positions, completed stories and preferred host on your device using UserDefaults. It does not contain advertising or analytics SDKs and does not create an account.\n\nConnecting a feed sends normal network requests, including your IP address, to the server you configure. Opening source links is subject to the destination’s privacy policy. Production privacy terms must name the operating company and its data processors before launch.") }
                    Button("Delete local listening data", role: .destructive) { reset = true }
                }
                Section { Button("Show welcome again") { onboarded = false; dismiss() }; Text("Sound Science 0.1 · Stay a little curious.").font(.caption) }
            }.navigationTitle("Settings").toolbar { Button("Done") { dismiss() } }
                .sheet(isPresented: $plus) { PlusView() }
                .confirmationDialog("Delete saved stories, queue and listening history?", isPresented: $reset, titleVisibility: .visible) { Button("Delete local data", role: .destructive) { player.clearListeningData(); library.saved = []; library.history = []; UserDefaults.standard.removeObject(forKey: "saved"); UserDefaults.standard.removeObject(forKey: "history") } }
        }
    }
}
struct PolicyView: View {
    var title: String
    var text: String
    var body: some View { ScrollView { VStack(alignment: .leading, spacing: 24) { Text(title).font(.system(size: 36, design: .serif)); Text(text).lineSpacing(6) }.padding(25) }.background(ScienceBreak.paper) }
}
struct PlusView: View {
    @Environment(\.dismiss) var dismiss
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Eyebrow(text: "SOUND SCIENCE PLUS")
                Text("A bigger orbit.").font(.system(size: 42, design: .serif))
                Text("Planned for launch: the complete archive, longer listening sessions and offline audio.").multilineTextAlignment(.center).foregroundStyle(ScienceBreak.muted)
                if let ids = Bundle.main.object(forInfoDictionaryKey: "ScienceBreakSubscriptionProducts") as? String, !ids.isEmpty {
                    SubscriptionStoreView(productIDs: ids.split(separator: ",").map(String.init))
                        .storeButton(.visible, for: .restorePurchases)
                } else {
                    Image(systemName: "sparkles").font(.system(size: 64, weight: .ultraLight)).frame(height: 130)
                    Text("Coming after the private beta").font(.headline)
                    Text("Purchases are not enabled in this build. All demo stories are free.").font(.subheadline).foregroundStyle(ScienceBreak.muted).multilineTextAlignment(.center)
                }
                Spacer()
            }.padding(28).background(ScienceBreak.paper).toolbar { Button("Done") { dismiss() } }
        }
    }
}
