import RiveRuntime
import SwiftUI

/// The animated cover used in the player: orbits turn, the sphere breathes and the
/// equalizer dances while audio plays, and everything settles when it pauses.
/// One Rive artboard serves every show — its gradient and play state are data-bound.
/// Source scene: rive/nowplaying/scene.rml (built with the Rive CLI).
@MainActor final class LivingCoverModel: ObservableObject {
    let rive: RiveViewModel?
    private var instance: RiveDataBindingViewModel.Instance?
    private var pending: (show: Show, playing: Bool)?

    init() {
        guard Bundle.main.url(forResource: "nowplaying", withExtension: "riv") != nil else { rive = nil; return }
        let model = RiveViewModel(fileName: "nowplaying", stateMachineName: "State Machine 1")
        rive = model
        model.riveModel?.enableAutoBind { [weak self] instance in
            guard let self else { return }
            self.instance = instance
            if let pending = self.pending { self.apply(show: pending.show, playing: pending.playing) }
        }
    }

    func apply(show: Show, playing: Bool) {
        guard let instance else { pending = (show, playing); return }
        instance.colorProperty(fromPath: "colorTop")?.value = UIColor(show.light)
        instance.colorProperty(fromPath: "colorBottom")?.value = UIColor(show.dark)
        instance.booleanProperty(fromPath: "isPlaying")?.value = playing
    }
}

struct LivingCover: View {
    var show: Show
    var playing: Bool
    var cornerRadius: CGFloat = 26
    @StateObject private var model = LivingCoverModel()

    var body: some View {
        Group {
            if let rive = model.rive {
                rive.view()
                    .aspectRatio(1, contentMode: .fit)
                    .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                    .onAppear { model.apply(show: show, playing: playing) }
                    .onChange(of: show) { _, new in model.apply(show: new, playing: playing) }
                    .onChange(of: playing) { _, new in model.apply(show: show, playing: new) }
            } else {
                ShowCover(show: show)  // the animation is optional; the static cover is the fallback
            }
        }
        .accessibilityHidden(true)
    }
}
