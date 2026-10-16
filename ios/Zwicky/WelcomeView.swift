import SwiftUI

/// Five steps: namesake, mission, process, followed shows, and account entry.
struct WelcomeView: View {
    @AppStorage("onboarded") private var onboarded = false
    @EnvironmentObject private var library: Library
    @EnvironmentObject private var player: AudioPlayer
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var step = 0
    @State private var advancing = true
    @State private var selected: Set<String> = Set(Show.all.prefix(4).map(\.id))
    @AccessibilityFocusState private var headingFocused: Bool


    var body: some View {
        VStack(spacing: 0) {
            header
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    switch step {
                    case 0: biography
                    case 1: mission
                    case 2: process
                    case 3: pickShows
                    default: login
                    }
                }
                .padding(.horizontal, 24).padding(.top, 12).padding(.bottom, 24)
                .frame(maxWidth: 600, alignment: .leading).frame(maxWidth: .infinity)
                .id(step)
                .transition(reduceMotion ? .opacity : .asymmetric(
                    insertion: .opacity.combined(with: .offset(x: advancing ? 32 : -32)),
                    removal: .opacity.combined(with: .offset(x: advancing ? -32 : 32))))
            }
            actions
        }
        .background(Theme.canvas.ignoresSafeArea())
        .foregroundStyle(Theme.ink)
        .interactiveDismissDisabled()
        .onAppear { player.pause() }
    }

    private var header: some View {
        HStack {
            if step > 0 {
                Button { go(to: step - 1) } label: { Image(systemName: "chevron.left").font(.body.weight(.semibold)).frame(width: 44, height: 44) }
                    .accessibilityLabel("Back")
            } else {
                Text("Zwicky").font(.system(size: 19, weight: .semibold, design: .serif)).frame(height: 44)
            }
            Spacer()
            HStack(spacing: 6) {
                ForEach(0..<5) { index in
                    Capsule().fill(index <= step ? Theme.ink : Theme.hairline).frame(width: index == step ? 22 : 6, height: 6)
                }
            }.accessibilityElement(children: .ignore).accessibilityLabel("Step \(step + 1) of 5")
            Spacer()
            Button(step < 4 ? "Skip" : "Guest") { if step < 4 { go(to: 4) } else { finish() } }.font(.subheadline).foregroundStyle(Theme.secondary).frame(minWidth: 44, minHeight: 44)
        }
        .padding(.horizontal, 20).padding(.top, 6)
    }

    private func title(_ text: String) -> some View {
        Text(text).font(.system(.largeTitle, design: .serif, weight: .semibold)).fixedSize(horizontal: false, vertical: true)
            .accessibilityAddTraits(.isHeader).accessibilityFocused($headingFocused)
    }

    init(initialStep: Int = 0) {
        _step = State(initialValue: min(4, max(0, initialStep)))
    }

    private var biography: some View {
        Group {
            Image("fritz-zwicky-pencil")
                .resizable().scaledToFit().aspectRatio(1, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .accessibilityLabel("Pencil portrait of Fritz Zwicky")
            title("Who was Zwicky?")
            Text("Fritz Zwicky was a Caltech astronomer who proposed dark matter and, with Walter Baade, linked supernovae to neutron stars. But many people have never heard of him. His dark matter proposal went largely unappreciated for decades, before becoming central to our understanding of the universe.")
                .font(.body).foregroundStyle(Theme.secondary)
            Link("Explore Zwicky’s legacy ↗", destination: URL(string: "https://burkeinstitute.caltech.edu/research/Legacy")!)
                .font(.caption).tint(Color(hex: 0xA74620))
        }
    }

    private var mission: some View {
        Group {
            editorialArt("OUR MISSION", symbol: "waveform")
            title("Discovery deserves\nto be shared.")
            Text("We highlight interesting scientific publications and the people behind them, turning research into stories more people can understand, learn from, and celebrate. Because scientific discovery deserves to be shared.")
                .font(.body).foregroundStyle(Theme.secondary)
            featureStrip
            Text("Learn something new. Celebrate discovery.").font(.system(.headline, design: .serif))
        }
    }

    private var process: some View {
        Group {
            editorialArt("HOW IT COMES TOGETHER", symbol: "waveform.path")
            title("From evidence\nto your ears.")
            Text("A little technology. A lot of curiosity.").foregroundStyle(Theme.secondary)
            VStack(alignment: .leading, spacing: 20) {
                point("doc.text.magnifyingglass", "01 · Start with scientific sources")
                point("text.quote", "02 · Shape an accessible story with AI")
                point("waveform", "03 · Give fictional hosts AI voices")
                point("link", "04 · Keep transcripts and sources attached")
            }
            Text("AI can make mistakes. Open the sources, explore the evidence, and keep asking questions.")
                .font(.caption).foregroundStyle(Theme.secondary)
        }
    }

    private func editorialArt(_ label: String, symbol: String) -> some View {
        ZStack(alignment: .bottomLeading) {
            Image(label == "OUR MISSION" ? "cover-wild-company" : label == "HOW IT COMES TOGETHER" ? "cover-gradient" : label == "YOUR NEXT CHAPTER" ? "cover-star-bros" : "cover-the-long-view").resizable().scaledToFill()
            LinearGradient(colors: [.clear, Color(hex: 0x092D30).opacity(0.85)], startPoint: .top, endPoint: .bottom)
            VStack(alignment: .leading, spacing: 12) {
                Image(systemName: symbol).font(.system(size: 32, weight: .light))
                Text(label).font(.system(.caption, design: .monospaced)).tracking(2)
            }.foregroundStyle(Color(hex: 0xF3E6C8)).padding(22)
        }
        .frame(height: 210).clipped()
        .clipShape(RoundedRectangle(cornerRadius: 8))
        .accessibilityHidden(true)
    }

    private var login: some View {
        Group {
            editorialArt("YOUR NEXT CHAPTER", symbol: "person.crop.circle")
            title("Make room\nfor wonder.")
            Text("Your shows are ready. Start listening and keep exploring.").foregroundStyle(Theme.secondary)
            Label("Sign in with Apple", systemImage: "apple.logo")
                .font(.headline).frame(maxWidth: .infinity, minHeight: 50)
                .foregroundStyle(Theme.secondary).background(Theme.subtle, in: Capsule())
                .accessibilityLabel("Sign in with Apple. Not available yet.")
            Text("Account login is coming soon. For now, your profile, followed shows, and listening history stay on this device.")
                .font(.caption).foregroundStyle(Theme.secondary)
        }
    }

    /// A curated strip, not a wall of every show, so the first screen explains the product.
    private var featureStrip: some View {
        let ids = ["the-long-view", "wild-company", "signal-and-noise", "common-ground", "star-bros"]
        let featured = ids.compactMap { id in Show.all.first { $0.id == id } }
        return ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach(Array(featured.enumerated()), id: \.element.id) { index, show in
                    ShowCover(show: show).frame(width: 116)
                        .motionEntrance(delay: Double(index) * 0.06)
                }
            }
            .padding(.vertical, 2)
        }
    }

    private func point(_ symbol: String, _ text: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: symbol).font(.body.weight(.medium)).frame(width: 36, height: 36).background(Theme.subtle, in: Circle())
            Text(text).font(.subheadline)
        }
    }

    private var pickShows: some View {
        Group {
            title("Follow your\nfavorite shows.")
            Text("Follow the ones that sound like you. You can change this anytime.").font(.body).foregroundStyle(Theme.secondary)
            LazyVGrid(columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)], spacing: 18) {
                ForEach(Show.all) { show in
                    let isOn = selected.contains(show.id)
                    Button {
                        Haptics.selection()
                        withAnimation(Motion.standard(reduceMotion: reduceMotion)) {
                            if isOn { selected.remove(show.id) } else { selected.insert(show.id) }
                        }
                    } label: {
                        VStack(alignment: .leading, spacing: 10) {
                            ShowCover(show: show)
                                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).strokeBorder(isOn ? Theme.ink : .clear, lineWidth: 3))
                                .overlay(alignment: .topTrailing) {
                                    Image(systemName: isOn ? "checkmark.circle.fill" : "circle")
                                        .font(.title2).symbolRenderingMode(.palette)
                                        .contentTransition(reduceMotion ? .opacity : .symbolEffect(.replace))
                                        .foregroundStyle(isOn ? .white : .white.opacity(0.9), isOn ? Theme.ink : .clear).padding(10)
                                }
                            HStack(spacing: 8) {
                                HostAvatar(host: show.host, size: 26)
                                VStack(alignment: .leading, spacing: 1) {
                                    Text(show.title).font(.subheadline.weight(.semibold)).lineLimit(1)
                                    Text(show.category).font(.caption).foregroundStyle(Theme.secondary).lineLimit(1)
                                    if library.episodes(of: show).isEmpty && !library.loading {
                                        Text("Episodes coming soon").font(.caption2).foregroundStyle(Theme.secondary)
                                    }
                                }
                            }
                        }
                    }
                    .buttonStyle(.pressable)
                    .accessibilityLabel("\(show.title), \(show.category), hosted by \(show.host.name)")
                    .accessibilityAddTraits(isOn ? .isSelected : [])
                }
            }
        }
    }

    private var actions: some View {
        Button {
            if step < 4 { go(to: step + 1) } else { finish() }
        } label: {
            Text(step == 3 ? (selected.isEmpty ? "Choose at least one show" : "Follow \(selected.count) show\(selected.count == 1 ? "" : "s")")
                 : step == 4 ? "Continue as guest" : "Continue")
        }
        .buttonStyle(PrimaryButtonStyle(fullWidth: true))
        .disabled(step == 3 && selected.isEmpty)
        .opacity(step == 3 && selected.isEmpty ? 0.4 : 1)
        .padding(.horizontal, 24).padding(.vertical, 12)
        .frame(maxWidth: 600).frame(maxWidth: .infinity)
        .background(Theme.canvas)
    }

    private func go(to next: Int) {
        advancing = next > step
        Haptics.selection()
        withAnimation(Motion.standard(reduceMotion: reduceMotion)) { step = next }
        headingFocused = true
    }

    private func finish() {
        Haptics.success()
        if !selected.isEmpty { library.setFollowing(selected) }
        if let first = Show.all.first(where: { selected.contains($0.id) }) { library.hostID = first.hostIDs.first ?? first.id }
        onboarded = true
    }
}
