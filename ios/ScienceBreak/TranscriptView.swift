import SwiftUI

/// Read-along transcript: words light up as they are spoken, the page follows the narrator,
/// and tapping a paragraph jumps the audio there. Set in Charter for long-form reading.
struct TranscriptView: View {
    @EnvironmentObject var player: AudioPlayer
    let story: Story
    let paragraphs: [TranscriptParagraph]
    @State private var following = true

    private var isCurrent: Bool { player.story?.id == story.id }
    private var now: Double { isCurrent ? player.position : -1 }
    private static let bodyFont = Theme.reading(21)
    private static let titleFont = Font.custom("Charter", size: 31, relativeTo: .title).weight(.bold)

    var body: some View {
        let active = activeParagraph(at: now)
        ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    HStack(spacing: 8) { HostAvatar(host: story.host, size: 24); Text("\(story.show.title) · \(story.host.name)").font(.subheadline).foregroundStyle(Theme.secondary) }
                    Text(story.title).font(Self.titleFont).foregroundStyle(Theme.ink)
                    ForEach(paragraphs.indices, id: \.self) { index in
                        Text(attributed(paragraphs[index], active: index == active))
                            .font(Self.bodyFont).lineSpacing(8)
                            .opacity(active < 0 || index == active ? 1 : 0.72)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .contentShape(Rectangle())
                            .onTapGesture { jump(to: index) }
                            .accessibilityAddTraits(.isButton)
                            .accessibilityHint("Plays from this paragraph")
                            .id(index)
                    }
                }
                .padding(.horizontal, 24).padding(.top, 12).padding(.bottom, 40)
            }
            .simultaneousGesture(DragGesture(minimumDistance: 12).onChanged { _ in following = false })
            .onChange(of: active) { _, index in
                guard following, index >= 0 else { return }
                withAnimation(.easeInOut(duration: 0.45)) { proxy.scrollTo(index, anchor: UnitPoint(x: 0.5, y: 0.28)) }
            }
            .onAppear { if active > 0 { proxy.scrollTo(active, anchor: UnitPoint(x: 0.5, y: 0.28)) } }
            .safeAreaInset(edge: .bottom) { controls(scrollBackTo: active, proxy: proxy) }
        }
        .background(Theme.canvas)
        .navigationBarTitleDisplayMode(.inline)
    }

    private func controls(scrollBackTo active: Int, proxy: ScrollViewProxy) -> some View {
        VStack(spacing: 10) {
            if !following && isCurrent && player.playing {
                Button {
                    following = true
                    withAnimation(.easeInOut(duration: 0.45)) { proxy.scrollTo(max(active, 0), anchor: UnitPoint(x: 0.5, y: 0.28)) }
                } label: { Label("Follow along", systemImage: "arrow.down.to.line").font(.caption.weight(.semibold)).padding(.horizontal, 14).frame(height: 34).background(Theme.surface, in: Capsule()).overlay(Capsule().strokeBorder(Theme.hairline)).shadow(color: .black.opacity(0.08), radius: 8, y: 3) }
                .foregroundStyle(Theme.ink)
            }
            HStack(spacing: 18) {
                Button { player.seek(player.position - 15) } label: { Image(systemName: "gobackward.15").frame(width: 44, height: 44) }
                    .disabled(!isCurrent).accessibilityLabel("Back 15 seconds")
                Button { isCurrent ? player.toggle() : player.play(story) } label: {
                    Image(systemName: isCurrent && player.playing ? "pause.fill" : "play.fill").font(.title3)
                        .frame(width: 54, height: 54).background(.white, in: Circle()).foregroundStyle(Theme.ink)
                }.accessibilityLabel(isCurrent && player.playing ? "Pause" : "Play")
                Button { player.seek(player.position + 15) } label: { Image(systemName: "goforward.15").frame(width: 44, height: 44) }
                    .disabled(!isCurrent).accessibilityLabel("Forward 15 seconds")
                VStack(alignment: .leading, spacing: 6) {
                    ProgressView(value: isCurrent ? min(player.position, player.duration) : 0, total: max(player.duration, 1)).tint(.white)
                    Text(isCurrent ? "\(clock(player.position)) / \(clock(player.duration))" : "Tap play or any paragraph")
                        .font(.caption2.monospacedDigit()).foregroundStyle(Color.white.opacity(0.7))
                }
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 16).padding(.vertical, 10)
            .background(Theme.ink, in: RoundedRectangle(cornerRadius: 26, style: .continuous))
        }
        .padding(.horizontal, 12).padding(.bottom, 6)
    }

    /// Index of the paragraph containing the most recently spoken word; -1 before playback.
    private func activeParagraph(at time: Double) -> Int {
        guard time >= 0 else { return -1 }
        return paragraphs.lastIndex { ($0.words.first?.start ?? .infinity) <= time } ?? 0
    }

    private func attributed(_ paragraph: TranscriptParagraph, active: Bool) -> AttributedString {
        let spokenCount = paragraph.words.lastIndex { $0.start <= now }.map { $0 + 1 } ?? 0
        var result = AttributedString()
        for (index, word) in paragraph.words.enumerated() {
            var piece = AttributedString(word.text)
            let spoken = index < spokenCount
            piece.foregroundColor = spoken ? Theme.ink : Theme.tertiary
            if active && index == spokenCount - 1 && isCurrent { piece.backgroundColor = story.show.light.opacity(0.35) }
            result += piece
            if index < paragraph.words.count - 1 { result += AttributedString(" ") }
        }
        return result
    }

    private func jump(to index: Int) {
        guard let start = paragraphs[index].words.first?.start else { return }
        following = true
        if !isCurrent || !player.hasLoadedAudio { player.play(story) }
        player.seek(max(0, start - 0.15))
        if !player.playing { player.resume() }
    }

    private func clock(_ time: Double) -> String { "\(Int(time) / 60):\(String(format: "%02d", Int(time) % 60))" }
}
