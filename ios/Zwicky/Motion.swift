import SwiftUI
import UIKit

/// Shared animation constants so motion feels consistent across the app.
enum Motion {
    /// The standard spring for state changes (rings, bars, toggles, appearing views).
    static let spring = Animation.spring(response: 0.42, dampingFraction: 0.82)
    /// A quicker, snappier spring for press feedback.
    static let press = Animation.spring(response: 0.24, dampingFraction: 0.72)
    /// Short, non-bouncy fallback used when Reduce Motion is on.
    static let gentle = Animation.easeInOut(duration: 0.2)

    /// The spring, or a plain fade-length ease when Reduce Motion is on.
    static func standard(reduceMotion: Bool) -> Animation { reduceMotion ? gentle : spring }
}

/// Thin wrapper over UIKit feedback generators.
@MainActor
enum Haptics {
    /// Light tap for play / pause.
    static func tap() {
        let generator = UIImpactFeedbackGenerator(style: .light)
        generator.impactOccurred()
    }
    /// Tick for toggles and pickers (follow, save, stepper).
    static func selection() {
        UISelectionFeedbackGenerator().selectionChanged()
    }
    /// Celebration, e.g. the daily goal being met.
    static func success() {
        UINotificationFeedbackGenerator().notificationOccurred(.success)
    }
}

/// Scales down slightly and dims while pressed, springing back on release.
/// Under Reduce Motion only the dim is applied.
struct PressableStyle: ButtonStyle {
    var scale: CGFloat = 0.96
    var dim: Double = 0.85
    func makeBody(configuration: Configuration) -> some View {
        PressableBody(configuration: configuration, scale: scale, dim: dim)
    }
}

private struct PressableBody: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let configuration: ButtonStyleConfiguration
    let scale: CGFloat
    let dim: Double
    var body: some View {
        configuration.label
            .scaleEffect(configuration.isPressed && !reduceMotion ? scale : 1)
            .opacity(configuration.isPressed ? dim : 1)
            .animation(reduceMotion ? Motion.gentle : Motion.press, value: configuration.isPressed)
    }
}

extension ButtonStyle where Self == PressableStyle {
    /// `.buttonStyle(.pressable)`
    static var pressable: PressableStyle { PressableStyle() }
}

/// A one-time reveal. Keep the layout fixed and use opacity alone for Reduce Motion.
private struct MotionEntrance: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var appeared = false
    var delay: Double

    func body(content: Content) -> some View {
        content
            .opacity(appeared || reduceMotion ? 1 : 0)
            .offset(y: appeared || reduceMotion ? 0 : 14)
            .onAppear {
                guard !appeared else { return }
                withAnimation(reduceMotion ? nil : Motion.spring.delay(delay)) { appeared = true }
            }
    }
}

/// Slow movement inside artwork, never on text or controls. The loop exists only
/// while visible and active, so switching tabs or backgrounding stops the work.
private struct LivingArtwork: ViewModifier {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.scenePhase) private var scenePhase
    @State private var visible = false

    func body(content: Content) -> some View {
        content
            .phaseAnimator(visible && scenePhase == .active && !reduceMotion ? [false, true] : [false]) { artwork, drift in
                artwork
                    .scaleEffect(reduceMotion ? 1 : (drift ? 1.08 : 1.03))
                    .offset(x: reduceMotion ? 0 : (drift ? 3 : -3), y: reduceMotion ? 0 : (drift ? -2 : 2))
            } animation: { _ in .easeInOut(duration: 7) }
            .onAppear { visible = true }
            .onDisappear { visible = false }
    }
}

/// A decorative listening motif for the welcome screen, not an audio meter.
struct ListeningSpark: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.scenePhase) private var scenePhase
    @State private var visible = false
    private let heights: [CGFloat] = [8, 16, 24, 12, 20, 14, 8]

    var body: some View {
        HStack(spacing: 4) {
            ForEach(heights.indices, id: \.self) { index in
                Capsule().fill(Theme.ink.opacity(index.isMultiple(of: 2) ? 0.8 : 0.4))
                    .frame(width: 4, height: heights[index])
                    .phaseAnimator(visible && scenePhase == .active && !reduceMotion ? [false, true] : [false]) { bar, pulse in
                        bar.scaleEffect(y: pulse ? 0.45 : 1, anchor: .center)
                    } animation: { _ in .easeInOut(duration: 0.65 + Double(index) * 0.13) }
            }
        }
        .accessibilityHidden(true)
        .onAppear { visible = true }
        .onDisappear { visible = false }
    }
}

extension View {
    func motionEntrance(delay: Double = 0) -> some View {
        modifier(MotionEntrance(delay: delay))
    }

    /// Apply before clipping to the artwork's shape.
    func livingArtwork() -> some View { modifier(LivingArtwork()) }

    /// Marks this view as the source of the iOS 18 zoom transition into the player. No-op on iOS 17.
    @ViewBuilder func playerZoomSource(id: String, in namespace: Namespace.ID?) -> some View {
        if #available(iOS 18, *), let namespace {
            self.matchedTransitionSource(id: id, in: namespace)
        } else {
            self
        }
    }

    /// Zooms the presented view out of the matching source on iOS 18. No-op on iOS 17 or without a namespace.
    @ViewBuilder func playerZoomDestination(id: String, in namespace: Namespace.ID?) -> some View {
        if #available(iOS 18, *), let namespace {
            self.navigationTransition(.zoom(sourceID: id, in: namespace))
        } else {
            self
        }
    }
}
