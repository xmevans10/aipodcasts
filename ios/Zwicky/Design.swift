import SwiftUI

/// Warm-neutral, general-purpose design tokens: quiet surfaces, hairlines and ink,
/// with colour reserved for each show's cover. Radii follow OpenAIKit.
enum Theme {
    static let canvas = Color(hex: 0xFAF9F6)
    static let surface = Color.white
    static let subtle = Color(hex: 0xF1EFEA)
    static let hairline = Color(hex: 0xE5E2DB)
    static let ink = Color(hex: 0x161614)
    static let secondary = Color(hex: 0x6B6964)
    static let tertiary = Color(hex: 0xA3A09A)
    static let display = Font.system(size: 30, weight: .semibold, design: .serif)
    static func reading(_ size: CGFloat) -> Font { .custom("Charter", size: size, relativeTo: .body) }
    /// Warm umber used for shadows so elevation reads as light on paper, not grey smudge.
    static let shadow = Color(hex: 0x3A2E1F)
    /// Faint top-edge light that makes a raised surface read as a physical sheet.
    static let highlight = Color.white
}

/// Elevation levels: each pairs a tight contact shadow with a wide ambient one.
enum Elevation {
    case flat, raised, floating

    var contact: (opacity: Double, radius: CGFloat, y: CGFloat) {
        switch self {
        case .flat: (0, 0, 0)
        case .raised: (0.06, 1.5, 1)
        case .floating: (0.08, 3, 2)
        }
    }
    var ambient: (opacity: Double, radius: CGFloat, y: CGFloat) {
        switch self {
        case .flat: (0, 0, 0)
        case .raised: (0.06, 14, 6)
        case .floating: (0.10, 28, 14)
        }
    }
}

extension View {
    /// Two stacked warm shadows: a crisp contact shadow plus a soft ambient falloff.
    func elevation(_ level: Elevation, tint: Color = Theme.shadow) -> some View {
        let c = level.contact, a = level.ambient
        return self
            .shadow(color: tint.opacity(c.opacity), radius: c.radius, x: 0, y: c.y)
            .shadow(color: tint.opacity(a.opacity), radius: a.radius, x: 0, y: a.y)
    }
}

/// A white sheet with a whisper of top light and an inner edge that catches it.
/// Flat surfaces keep the hairline since no shadow separates them.
struct SurfaceBackground: View {
    var radius: CGFloat
    var elevation: Elevation = .raised
    var body: some View {
        let shape = RoundedRectangle(cornerRadius: radius, style: .continuous)
        shape.fill(Theme.surface)
            .overlay(shape.fill(LinearGradient(colors: [Theme.highlight.opacity(0), Theme.canvas.opacity(0.55)],
                                               startPoint: .top, endPoint: .bottom)))
            .overlay {
                if elevation == .flat {
                    shape.strokeBorder(Theme.hairline)
                } else {
                    // Brighter along the top edge, fading to a barely-there warm edge below.
                    shape.strokeBorder(LinearGradient(colors: [Theme.highlight, Theme.hairline.opacity(0.35)],
                                                      startPoint: .top, endPoint: .bottom), lineWidth: 0.75)
                }
            }
            .elevation(elevation)
    }
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

struct PrimaryButtonStyle: ButtonStyle {
    var fullWidth = false
    /// A show's colours when the button belongs to one; ink otherwise.
    var show: Show? = nil
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(.white)
            .background {
                if let show {
                    Capsule().fill(LinearGradient(colors: [show.mid, show.dark], startPoint: .topLeading, endPoint: .bottomTrailing))
                } else {
                    Capsule().fill(Theme.ink)
                }
            }
            .overlay(Capsule().strokeBorder(LinearGradient(colors: [.white.opacity(0.28), .white.opacity(0)],
                                                           startPoint: .top, endPoint: .center), lineWidth: 0.75))
            .shadow(color: (show?.dark ?? Theme.ink).opacity(configuration.isPressed ? 0.14 : 0.22),
                    radius: configuration.isPressed ? 3 : 10, y: configuration.isPressed ? 1 : 5)
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .brightness(configuration.isPressed ? -0.04 : 0)
            .animation(.spring(response: 0.28, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    var fullWidth = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(Theme.ink)
            .background(.ultraThinMaterial, in: Capsule())
            .background(Theme.surface.opacity(0.5), in: Capsule())
            .overlay(Capsule().strokeBorder(LinearGradient(colors: [Theme.highlight.opacity(0.9), Theme.hairline.opacity(0.8)],
                                                           startPoint: .top, endPoint: .bottom), lineWidth: 0.75))
            .elevation(configuration.isPressed ? .flat : .raised)
            .scaleEffect(configuration.isPressed ? 0.97 : 1)
            .animation(.spring(response: 0.28, dampingFraction: 0.7), value: configuration.isPressed)
    }
}

struct SectionHeader<Trailing: View>: View {
    var title: String
    @ViewBuilder var trailing: Trailing
    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title).font(.title3.weight(.semibold)).foregroundStyle(Theme.ink).accessibilityAddTraits(.isHeader)
            Spacer()
            trailing.font(.subheadline.weight(.medium)).foregroundStyle(Theme.secondary)
        }
    }
}
extension SectionHeader where Trailing == EmptyView {
    init(title: String) { self.title = title; self.trailing = EmptyView() }
}

/// Podcast cover art: an organic mesh wash, a faint per-show line motif, film grain,
/// a soft light bloom and the show title set in serif. No glyph watermark.
/// Size it with `.frame(width:)`; it stays square.
struct ShowCover: View {
    var show: Show
    var body: some View {
        GeometryReader { geometry in
            // Always square, whatever the parent proposes: a cover that stretches drags
            // the row's text on top of it.
            let w = min(geometry.size.width, geometry.size.height)
            ZStack(alignment: .bottomLeading) {
                // Every decorative layer is clamped to w×w so none of them can size the cover.
                Image("cover-\(show.id)")
                    .resizable()
                    .scaledToFill()
                    .frame(width: w, height: w)
                RadialGradient(colors: [show.light.opacity(0.4), .clear], center: UnitPoint(x: 0.82, y: 0.14),
                               startRadius: 0, endRadius: w * 0.72)
                Ellipse()
                    .fill(LinearGradient(colors: [.white.opacity(0.18), .clear], startPoint: .top, endPoint: .bottom))
                    .frame(width: w * 1.5, height: w * 0.42)
                    .rotationEffect(.degrees(-26))
                    .offset(x: -w * 0.18, y: w * 0.2)
                    // Clamped to the cover: the sheen is wider than the art, and without this
                    // the stack sizes itself to the sheen and shifts everything else off-centre.
                    .frame(width: w, height: w)
                if w >= 96 {
                    // A low shade behind the title keeps white type legible over the lightest mesh.
                    LinearGradient(stops: [.init(color: show.dark.opacity(0.5), location: 0),
                                           .init(color: .clear, location: 0.55)],
                                   startPoint: .bottom, endPoint: .top)
                        .frame(width: w, height: w)
                }
                // Printed, not digital: fine grain, overlay-blended within the compositing group.
                CoverGrain().frame(width: w, height: w).blendMode(.overlay).opacity(w >= 96 ? 0.2 : 0.14)
                if w >= 96 {
                    // The trailing spacer pins the block left and stops a long title
                    // laying itself out wider than the art and spilling past both edges.
                    HStack(alignment: .bottom, spacing: 0) {
                        VStack(alignment: .leading, spacing: w * 0.025) {
                            Text(show.title).font(.system(size: w * 0.125, weight: .semibold, design: .serif)).tracking(-0.3)
                                .lineLimit(2).minimumScaleFactor(0.7)
                                .fixedSize(horizontal: false, vertical: true)
                            Text(show.host.name.uppercased()).font(.system(size: max(7, w * 0.046), weight: .semibold))
                                .tracking(0.9).opacity(0.85).lineLimit(1)
                        }
                        Spacer(minLength: 0)
                    }
                    .foregroundStyle(.white).shadow(color: show.dark.opacity(0.4), radius: w * 0.05, y: w * 0.01)
                    .frame(width: w * 0.86)
                    .padding(.horizontal, w * 0.07)
                    .padding(.bottom, w * 0.07)
                }
            }
            .frame(width: w, height: w)
            // An overlay cannot change the cover's size, so the host never stretches the art.
            .overlay(alignment: w >= 96 ? .topTrailing : .center) {
                HostAvatar(host: show.host, size: w >= 96 ? w * 0.3 : w * 0.46)
                    .overlay(Circle().strokeBorder(.white.opacity(0.7), lineWidth: max(1, w * 0.012)))
                    .shadow(color: show.dark.opacity(0.35), radius: w * 0.04, y: w * 0.012)
                    .padding(w >= 96 ? w * 0.07 : 0)
            }
            // Keeps the bloom and sheen inside the cover instead of compositing with the card behind it.
            .compositingGroup()
            .clipShape(RoundedRectangle(cornerRadius: max(6, w * 0.11), style: .continuous))
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .aspectRatio(1, contentMode: .fit)
        .accessibilityHidden(true)
    }
}

struct StatTile: View {
    var value: String
    var label: String
    var symbol: String
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Image(systemName: symbol).font(.footnote.weight(.semibold)).foregroundStyle(Theme.secondary)
            Text(value).font(.system(size: 26, weight: .semibold, design: .rounded)).monospacedDigit().foregroundStyle(Theme.ink)
            Text(label).font(.caption).foregroundStyle(Theme.secondary).lineLimit(1).minimumScaleFactor(0.75)
        }
        .padding(14).frame(maxWidth: .infinity, alignment: .leading)
        .background(SurfaceBackground(radius: OpenAIKit.Radius.card, elevation: .raised))
        .accessibilityElement(children: .combine)
    }
}

extension View {
    /// White card lifted off the canvas by a soft two-layer shadow (hairline only when `.flat`).
    func card(padding: CGFloat = 16, radius: CGFloat = OpenAIKit.Radius.panel, elevation: Elevation = .raised) -> some View {
        self.padding(padding)
            .background(SurfaceBackground(radius: radius, elevation: elevation))
    }
}
