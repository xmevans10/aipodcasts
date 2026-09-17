import SwiftUI
import AVFoundation

/// Short, explicitly labelled device narration, separate from listening history and the main player.
@MainActor private final class HostIntroduction: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    @Published private(set) var speaking = false
    private let synthesizer = AVSpeechSynthesizer()
    private var active: AVSpeechUtterance?
    override init() { super.init(); synthesizer.delegate = self }
    func stop() { active = nil; synthesizer.stopSpeaking(at: .immediate); speaking = false }
    func play(_ host: Host) {
        stop()
        let lines = [
            "nova": "I'm Mira. Let's take the scenic route through the universe. Big questions, strange physics, and a little cosmic perspective.",
            "fern": "I'm Clara. There is a whole world hiding in the ordinary. Let's follow the roots, the wings, and the wonderfully unexpected connections.",
            "ada": "I'm Elias. Brains, machines, and the interesting mess in between. Let's ask a better question, and see where the evidence takes us.",
            "atlas": "I'm Theo. Behind every discovery, there is a human story. Let's meet the ideas, the accidents, and the people who changed how we see."
        ]
        let utterance = AVSpeechUtterance(string: lines[host.id] ?? host.personality)
        utterance.voice = AVSpeechSynthesisVoice(language: host.id == "nova" ? "en-GB" : "en-US")
        utterance.rate = AVSpeechUtteranceDefaultSpeechRate * 0.92
        active = utterance; speaking = true; synthesizer.speak(utterance)
    }
    nonisolated func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        Task { @MainActor in if self.active === utterance { self.speaking = false; self.active = nil } }
    }
}

struct WelcomeView: View {
    @AppStorage("onboarded") private var onboarded = false
    @EnvironmentObject private var library: Library
    @EnvironmentObject private var player: AudioPlayer
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.scenePhase) private var scenePhase
    @StateObject private var introduction = HostIntroduction()
    @State private var step = 0
    @State private var selectedID = "nova"
    @AccessibilityFocusState private var headingFocused: Bool
    @ScaledMetric(relativeTo: .largeTitle) private var titleSize = 43
    private var host: Host { Host.all.first { $0.id == selectedID } ?? Host.all[0] }
    private var firstStory: Story? { library.stories.first { $0.hostID == selectedID } }
    private var dark: Bool { step == 0 }
    private var foreground: Color { dark ? ScienceBreak.paper : ScienceBreak.ink }

    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollView {
                VStack(alignment: .leading, spacing: 25) {
                    Group {
                        switch step {
                        case 0: welcome
                        case 1: hosts
                        default: ready
                        }
                    }
                }
                .padding(.horizontal, 25).padding(.top, 18).padding(.bottom, 24)
                .frame(maxWidth: 600, alignment: .leading).frame(maxWidth: .infinity)
                .id(step).transition(.opacity.combined(with: .offset(y: reduceMotion ? 0 : 12)))
            }
            actions
        }
        .background((dark ? ScienceBreak.ink : ScienceBreak.paper).ignoresSafeArea())
        .foregroundStyle(foreground)
        .interactiveDismissDisabled()
        .onAppear { selectedID = library.hostID; player.pause() }
        .onDisappear { introduction.stop() }
        .onChange(of: scenePhase) { _, phase in if phase != .active { introduction.stop() } }
    }

    private var header: some View {
        HStack(alignment: .center) {
            if step > 0 {
                Button { navigate(to: step - 1) } label: {
                    Image(systemName: "arrow.left").frame(width: 44, height: 44)
                }.accessibilityLabel("Previous step")
            } else {
                Text("Sound Science.").font(.system(size: 25, weight: .bold, design: .serif)).tracking(-1).lineLimit(1).minimumScaleFactor(0.75)
            }
            Spacer()
            HStack(spacing: 6) {
                ForEach(0..<3) { index in
                    Capsule().fill(index <= step ? (dark ? ScienceBreak.acid : ScienceBreak.ink) : foreground.opacity(0.15))
                        .frame(width: index == step ? 28 : 7, height: 5)
                }
            }.accessibilityElement(children: .ignore).accessibilityLabel("Step \(step + 1) of 3")
            Spacer()
            Button("Skip") { finish(play: false) }
                .font(.subheadline).foregroundStyle(foreground.opacity(0.75)).frame(minWidth: 44, minHeight: 44)
                .accessibilityLabel("Skip setup and explore ScienceBreak")
        }.padding(.horizontal, 25).padding(.top, 8).padding(.bottom, 6)
    }

    private func overline(_ text: String) -> some View {
        Text(text).font(.system(.caption2, design: .monospaced).weight(.semibold))
            .tracking(1.6).foregroundStyle(dark ? ScienceBreak.acid : ScienceBreak.muted)
    }
    private func title(_ text: String) -> some View {
        Text(text).font(.system(size: titleSize, weight: .regular, design: .serif))
            .tracking(-1.4).fixedSize(horizontal: false, vertical: true)
            .accessibilityAddTraits(.isHeader).accessibilityFocused($headingFocused)
    }

    private var welcome: some View {
        Group {
            overline("LESS SCROLL. MORE WONDER.")
            title("The world is weird.\nStay curious.")
            ZStack(alignment: .bottomLeading) {
                OrbitalArt(hue: 0.66)
                VStack(alignment: .leading, spacing: 8) {
                    Label("A LITTLE MORE CURIOUS", systemImage: "headphones")
                        .font(.system(.caption2, design: .monospaced).weight(.semibold)).tracking(1)
                    Text("Big ideas.\nEasy listening.")
                        .font(.system(.title, design: .serif)).foregroundStyle(ScienceBreak.ink)
                }.padding(22).frame(maxWidth: .infinity, alignment: .leading)
                    .background(LinearGradient(colors: [ScienceBreak.paper.opacity(0), ScienceBreak.paper.opacity(0.95)], startPoint: .top, endPoint: .bottom))
            }.frame(height: 265).clipShape(RoundedRectangle(cornerRadius: 28)).foregroundStyle(ScienceBreak.ink)
            Text("Small stories. Big rabbit holes. Science for your walk, your commute, your just-one-more minute.")
                .font(.body).lineSpacing(4).foregroundStyle(ScienceBreak.paper.opacity(0.78))
            HStack(spacing: 12) {
                Image(systemName: "quote.opening").foregroundStyle(ScienceBreak.acid)
                Text("Real sources. Fresh perspectives. Zero doomscroll.").font(.subheadline)
            }
        }
    }

    private var hosts: some View {
        Group {
            overline("01 / FIND YOUR FREQUENCY")
            title("Your kind\nof curious.")
            Text("Choose the voice of your next rabbit hole. We'll bring their stories to the top.")
                .font(.body).foregroundStyle(ScienceBreak.muted).lineSpacing(3)
            VStack(spacing: 10) {
                ForEach(Host.all) { item in hostOption(item) }
            }
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Label("MEET \(host.name.components(separatedBy: " ")[0].uppercased())", systemImage: "waveform")
                        .font(.system(.caption2, design: .monospaced).weight(.semibold)).tracking(1)
                    Spacer()
                    Button {
                        if introduction.speaking { introduction.stop() } else { introduction.play(host) }
                    } label: {
                        Image(systemName: introduction.speaking ? "stop.fill" : "play.fill")
                            .frame(width: 46, height: 46).background(ScienceBreak.ink, in: Circle()).foregroundStyle(ScienceBreak.paper)
                    }.accessibilityLabel(introduction.speaking ? "Stop introduction" : "Hear \(host.name)'s introduction")
                }
                Text(host.personality).font(.system(.title3, design: .serif))
                Text("Device voice sample · Fictional AI host").font(.caption).foregroundStyle(ScienceBreak.muted)
            }.padding(18).background(host.color.opacity(0.3), in: RoundedRectangle(cornerRadius: 20))
            Text("All four hosts are yours to explore. You can change your favorite anytime.")
                .font(.caption).foregroundStyle(ScienceBreak.muted)
        }
    }

    private func hostOption(_ item: Host) -> some View {
        let selected = selectedID == item.id
        return Button {
            introduction.stop()
            withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.2)) { selectedID = item.id }
        } label: {
            HStack(spacing: 14) {
                HostAvatar(host: item, size: 48)
                VStack(alignment: .leading, spacing: 4) {
                    Text(item.name).font(.system(.title3, design: .serif))
                    Text(item.niche).font(.subheadline).foregroundStyle(ScienceBreak.muted)
                }
                Spacer(minLength: 5)
                Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                    .font(.title3).foregroundStyle(selected ? ScienceBreak.ink : ScienceBreak.muted.opacity(0.4))
            }.padding(15).frame(maxWidth: .infinity, alignment: .leading)
                .background(selected ? item.color.opacity(0.16) : .white.opacity(0.55), in: RoundedRectangle(cornerRadius: 20))
                .overlay(RoundedRectangle(cornerRadius: 20).strokeBorder(selected ? ScienceBreak.ink : ScienceBreak.ink.opacity(0.09), lineWidth: selected ? 1.5 : 1))
                .contentShape(RoundedRectangle(cornerRadius: 20))
        }.buttonStyle(.plain).accessibilityLabel("\(item.name), \(item.niche)")
            .accessibilityAddTraits(selected ? .isSelected : [])
    }

    private var ready: some View {
        Group {
            overline("02 / PRESS PLAY ON SOMETHING GOOD")
            title("A little wonder,\ncoming right up.")
            if let story = firstStory {
                VStack(alignment: .leading, spacing: 0) {
                    OrbitalArt(hue: host.hue).frame(height: 200)
                        .overlay(alignment: .bottomLeading) {
                            Text(story.isDemo ? "YOUR FIRST DEMO STORY" : "YOUR FIRST LISTEN")
                                .font(.system(.caption2, design: .monospaced).weight(.semibold)).tracking(1)
                                .padding(10).background(ScienceBreak.acid, in: Capsule()).padding(16)
                        }
                    VStack(alignment: .leading, spacing: 16) {
                        overline("\(story.topic) / \(story.minutes) MIN LISTEN")
                        Text(story.title).font(.system(.title, design: .serif)).fixedSize(horizontal: false, vertical: true)
                        Text(story.dek).font(.subheadline).foregroundStyle(ScienceBreak.muted)
                        HStack(spacing: 10) {
                            HostAvatar(host: host, size: 32)
                            Text("With \(host.name)").font(.subheadline)
                        }
                    }.padding(22)
                }.background(.white.opacity(0.75), in: RoundedRectangle(cornerRadius: 26))
                    .clipShape(RoundedRectangle(cornerRadius: 26))
                Label(story.isDemo ? "Original demo story · Device narration" : "AI-assisted story · Synthetic narration", systemImage: "waveform")
                    .font(.caption).foregroundStyle(ScienceBreak.muted)
            } else {
                HostAvatar(host: host, size: 100)
                Text("You're in \(host.name)'s orbit. Explore the current edition while their next story takes shape.")
                    .font(.body).foregroundStyle(ScienceBreak.muted)
            }
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: "text.book.closed").font(.title3)
                VStack(alignment: .leading, spacing: 5) {
                    Text("Curiosity, with receipts.").font(.subheadline.weight(.semibold))
                    Text("Read along, follow the sources, and see what the evidence can—and can't—tell us.")
                        .font(.subheadline).foregroundStyle(ScienceBreak.muted)
                }
            }
        }
    }

    private var actions: some View {
        VStack(spacing: 9) {
            Button {
                if step < 2 { navigate(to: step + 1) } else { finish(play: firstStory != nil) }
            } label: {
                HStack {
                    Text(step == 0 ? "Find my frequency" : step == 1 ? "Continue with \(host.name.components(separatedBy: " ")[0])" : firstStory == nil ? "Explore ScienceBreak" : "Start my first listen")
                    Spacer(minLength: 12)
                    Image(systemName: step == 2 && firstStory != nil ? "play.fill" : "arrow.right")
                }.frame(maxWidth: .infinity)
            }.buttonStyle(CapsuleButton(light: true))
            if step == 2 {
                Button("I'll explore first") { finish(play: false) }
                    .font(.subheadline).frame(minHeight: 44)
            } else {
                Text(step == 0 ? "No account. No paywall. Just curiosity." : "A favorite, not a commitment.")
                    .font(.caption).foregroundStyle(foreground.opacity(0.65)).padding(.vertical, 6)
            }
        }.padding(.horizontal, 25).padding(.top, 12).padding(.bottom, 10)
            .frame(maxWidth: 600).frame(maxWidth: .infinity)
            .background(dark ? ScienceBreak.ink : ScienceBreak.paper)
    }

    private func navigate(to next: Int) {
        introduction.stop()
        withAnimation(reduceMotion ? nil : .easeInOut(duration: 0.3)) { step = next }
        headingFocused = true
    }
    private func finish(play: Bool) {
        introduction.stop()
        library.hostID = selectedID
        if play, let story = firstStory { player.play(story) }
        onboarded = true
    }
}
