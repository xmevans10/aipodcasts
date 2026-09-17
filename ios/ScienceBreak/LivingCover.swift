import RiveRuntime
import SwiftUI

/// The animated player cover. One Rive artboard serves every show: the app writes the
/// show's gradient once, then pushes five band levels and an overall level every frame
/// from the episode's own audio envelope, so the bars, sphere and halo move with the
/// narration instead of looping. Source scene: rive/nowplaying/scene.rml.
@MainActor final class LivingCoverModel: ObservableObject {
    let rive: RiveViewModel?
    private var instance: RiveDataBindingViewModel.Instance?
    private var pendingColors: Show?
    private var levels: [[Double]] = []
    private var hop = 0.1
    private var smoothed = [Double](repeating: 0, count: 6)
    private var ticker: Timer?

    init() {
        guard Bundle.main.url(forResource: "nowplaying", withExtension: "riv") != nil else { rive = nil; return }
        let model = RiveViewModel(fileName: "nowplaying", stateMachineName: "State Machine 1")
        rive = model
        model.riveModel?.enableAutoBind { [weak self] instance in
            guard let self else { return }
            self.instance = instance
            if let show = self.pendingColors { self.apply(show: show) }
        }
    }

    deinit { ticker?.invalidate() }

    func apply(show: Show) {
        guard let instance else { pendingColors = show; return }
        instance.colorProperty(fromPath: "colorTop")?.value = UIColor(show.light)
        instance.colorProperty(fromPath: "colorBottom")?.value = UIColor(show.dark)
    }

    func load(story: Story?) {
        guard let story, let track = Episodes.levels(for: story.id) else { levels = []; return }
        levels = track.frames
        hop = track.hop
    }

    /// Drives the scene at 30fps while audio plays; decays to rest when it stops.
    func follow(position: @escaping () -> Double, playing: Bool) {
        ticker?.invalidate()
        instance?.booleanProperty(fromPath: "isPlaying")?.value = playing
        guard playing else { decay(); return }
        ticker = Timer.scheduledTimer(withTimeInterval: 1.0 / 30, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.push(at: position()) }
        }
    }

    private func frame(at seconds: Double) -> [Double] {
        guard !levels.isEmpty else { return [] }
        let index = max(0, min(levels.count - 1, Int(seconds / hop)))
        return levels[index]
    }

    private func push(at seconds: Double) {
        guard let instance else { return }
        let bands = frame(at: seconds)
        guard bands.count >= 5 else { return }
        let overall = bands.reduce(0, +) / Double(bands.count)
        for (index, target) in (bands + [overall]).enumerated() {
            // fast attack, slow release: peaks land, tails fall away smoothly
            let rate = target > smoothed[index] ? 0.55 : 0.18
            smoothed[index] += (target - smoothed[index]) * rate
        }
        write()
    }

    private func decay() {
        ticker = Timer.scheduledTimer(withTimeInterval: 1.0 / 30, repeats: true) { [weak self] _ in
            Task { @MainActor in
                guard let self else { return }
                for index in self.smoothed.indices { self.smoothed[index] *= 0.82 }
                self.write()
                if self.smoothed.allSatisfy({ $0 < 0.01 }) { self.ticker?.invalidate(); self.ticker = nil }
            }
        }
    }

    private func write() {
        guard let instance else { return }
        for band in 0..<5 { instance.numberProperty(fromPath: "band\(band + 1)")?.value = Float(smoothed[band]) }
        instance.numberProperty(fromPath: "level")?.value = Float(smoothed[5])
    }
}

struct LivingCover: View {
    var show: Show
    var story: Story?
    var playing: Bool
    var position: () -> Double
    var cornerRadius: CGFloat = 26
    @StateObject private var model = LivingCoverModel()

    var body: some View {
        Group {
            if let rive = model.rive {
                rive.view()
                    .aspectRatio(1, contentMode: .fit)
                    .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                    .onAppear {
                        model.apply(show: show)
                        model.load(story: story)
                        model.follow(position: position, playing: playing)
                    }
                    .onChange(of: show) { _, new in model.apply(show: new) }
                    .onChange(of: story?.id) { _, _ in
                        model.load(story: story)
                        model.follow(position: position, playing: playing)
                    }
                    .onChange(of: playing) { _, new in model.follow(position: position, playing: new) }
                    .onDisappear { model.follow(position: position, playing: false) }
            } else {
                ShowCover(show: show)  // the animation is optional; the static cover is the fallback
            }
        }
        .accessibilityHidden(true)
    }
}
