import SwiftUI
import UIKit

// Colour as environment: helpers that let a show's colours fill the page around
// its content instead of living only inside the cover square.

/// A show's colour field: a `mid` → `dark` wash, a soft `light` bloom and a dark scrim
/// so white text on top stays legible even for the brightest shows.
struct ShowWash: View {
    var show: Show
    /// Where the light bloom sits (unit coordinates).
    var glow: UnitPoint? = UnitPoint(x: 0.5, y: 0.22)
    var body: some View {
        ZStack {
            LinearGradient(colors: [show.mid, show.dark], startPoint: .top, endPoint: .bottom)
            if let glow {
                RadialGradient(colors: [show.light.opacity(0.55), .clear], center: glow, startRadius: 0, endRadius: 320)
            }
            // Scrim: keeps white text AA-legible on the lighter mids (green, teal).
            LinearGradient(colors: [.black.opacity(0.12), .black.opacity(0.3)], startPoint: .top, endPoint: .bottom)
        }
    }
}

/// A full-bleed header background: the show wash, extended far upwards so it fills
/// the status and navigation bars (and pull-down overscroll), then a fade into the canvas.
/// Use as `.background(alignment: .bottom) { ImmersiveHeaderBackground(show:, fade:) }`
/// on content whose bottom `fade` points are left empty.
struct ImmersiveHeaderBackground: View {
    var show: Show
    var fade: CGFloat = 96
    var body: some View {
        VStack(spacing: 0) {
            // Under the bars and the pull-down bounce: the wash's top colour, continued.
            show.mid.mix(.black, 0.12).frame(height: 600)
            ShowWash(show: show, glow: nil)
            LinearGradient(stops: [
                .init(color: show.dark.mix(.black, 0.3), location: 0),
                .init(color: show.dark.mix(.black, 0.3), location: 0.2),
                .init(color: show.dark.opacity(0.5), location: 0.55),
                .init(color: Theme.canvas.opacity(0), location: 1),
            ], startPoint: .top, endPoint: .bottom)
            .frame(height: fade)
        }
        // Grows upwards past the top of the content by the extension's height.
        .padding(.top, -600)
        .accessibilityHidden(true)
    }
}

/// Soft blurred colour glow to sit behind a cover or artwork.
struct CoverGlow: View {
    var show: Show
    var size: CGFloat
    var body: some View {
        ZStack {
            Circle().fill(show.light).frame(width: size, height: size).offset(x: size * 0.12, y: -size * 0.08)
            Circle().fill(show.mid).frame(width: size * 0.8, height: size * 0.8).offset(x: -size * 0.14, y: size * 0.1)
        }
        .blur(radius: size * 0.22)
        .opacity(0.85)
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }
}

/// Primary action on a coloured field: a white capsule with the show's dark ink.
struct OnColorPrimaryButtonStyle: ButtonStyle {
    var show: Show
    var fullWidth = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(show.dark).background(.white, in: Capsule())
            .opacity(configuration.isPressed ? 0.75 : 1)
    }
}

/// Secondary action on a coloured field: translucent white glass with white text.
struct OnColorSecondaryButtonStyle: ButtonStyle {
    var fullWidth = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(.white)
            .background(.white.opacity(configuration.isPressed ? 0.26 : 0.16), in: Capsule())
            .overlay(Capsule().strokeBorder(.white.opacity(0.28)))
    }
}

extension View {
    /// Navigation bar for a page whose header is filled with a show's colour: the bar is
    /// transparent over the header, turns solid `show.dark` once the header has scrolled
    /// away (`solid`), and always carries a white back button and (when solid) title.
    func immersiveNavigationBar(show: Show, title: String, solid: Bool) -> some View {
        modifier(ImmersiveNavigationBar(show: show, title: title, solid: solid))
    }
}

private struct ImmersiveNavigationBar: ViewModifier {
    var show: Show
    var title: String
    var solid: Bool
    @Environment(\.dismiss) private var dismiss
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    func body(content: Content) -> some View {
        content
            .navigationBarTitleDisplayMode(.inline)
            // The system back button takes the app's ink tint, which vanishes on the
            // colour; this one is always white. Swipe-back is kept by the extension below.
            .navigationBarBackButtonHidden(true)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button { dismiss() } label: {
                        Image(systemName: "chevron.left").font(.body.weight(.semibold)).foregroundStyle(.white)
                            .frame(width: 34, height: 34)
                            .background(.black.opacity(solid ? 0 : 0.18), in: Circle())
                            .frame(minWidth: 44, minHeight: 44)
                    }.accessibilityLabel("Back")
                }
                ToolbarItem(placement: .principal) {
                    Text(title).font(.headline).foregroundStyle(.white).lineLimit(1)
                        .opacity(solid ? 1 : 0).accessibilityHidden(!solid)
                }
            }
            .toolbarBackground(show.dark, for: .navigationBar)
            .toolbarBackground(solid ? .visible : .hidden, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
            .animation(reduceMotion ? nil : .easeOut(duration: 0.2), value: solid)
    }
}

/// Reports when a header's bottom edge has scrolled up under the navigation bar.
struct HeaderScrollTracker: ViewModifier {
    @Binding var passed: Bool
    /// How far below the scroll view's top the header bottom must stay to count as visible.
    var threshold: CGFloat = 110
    func body(content: Content) -> some View {
        content.onGeometryChange(for: Bool.self) { proxy in
            proxy.frame(in: .scrollView).maxY < threshold
        } action: { passed = $0 }
    }
}

/// Now-playing environment: the show's deep wash with two drifting blooms of its colours,
/// darkened towards the bottom so the controls always read in white.
struct PlayerBackdrop: View {
    var show: Show
    var body: some View {
        GeometryReader { geometry in
            let w = geometry.size.width
            ZStack {
                LinearGradient(colors: [show.mid, show.dark, show.dark.mix(.black, 0.35)], startPoint: .top, endPoint: .bottom)
                Circle().fill(show.light).frame(width: w * 1.1).blur(radius: w * 0.28).opacity(0.55)
                    .position(x: w * 0.78, y: geometry.size.height * 0.12)
                Circle().fill(show.mid).frame(width: w * 1.2).blur(radius: w * 0.3).opacity(0.7)
                    .position(x: w * 0.1, y: geometry.size.height * 0.45)
                // Scrim: white text stays AA on the brightest mids (green, teal).
                LinearGradient(colors: [.black.opacity(0.1), .black.opacity(0.2), .black.opacity(0.4)], startPoint: .top, endPoint: .bottom)
            }
        }
        .accessibilityHidden(true)
    }
}

extension Color {
    /// Blend towards another colour by `amount` (0…1), in sRGB.
    func mix(_ other: Color, _ amount: Double) -> Color {
        let a = UIColor(self), b = UIColor(other)
        var (r1, g1, b1, a1): (CGFloat, CGFloat, CGFloat, CGFloat) = (0, 0, 0, 0)
        var (r2, g2, b2, a2): (CGFloat, CGFloat, CGFloat, CGFloat) = (0, 0, 0, 0)
        a.getRed(&r1, green: &g1, blue: &b1, alpha: &a1)
        b.getRed(&r2, green: &g2, blue: &b2, alpha: &a2)
        let t = CGFloat(amount)
        return Color(red: Double(r1 + (r2 - r1) * t), green: Double(g1 + (g2 - g1) * t),
                     blue: Double(b1 + (b2 - b1) * t), opacity: Double(a1 + (a2 - a1) * t))
    }
}

/// Hiding the system back button also disables the edge swipe; restore it for any
/// pushed screen.
extension UINavigationController: UIGestureRecognizerDelegate {
    override open func viewDidLoad() {
        super.viewDidLoad()
        interactivePopGestureRecognizer?.delegate = self
    }
    public func gestureRecognizerShouldBegin(_ gestureRecognizer: UIGestureRecognizer) -> Bool {
        viewControllers.count > 1
    }
}
