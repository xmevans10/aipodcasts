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
            .opacity(configuration.isPressed ? 0.75 : 1)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    var fullWidth = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(Theme.ink).background(Theme.surface, in: Capsule())
            .overlay(Capsule().strokeBorder(Theme.hairline))
            .opacity(configuration.isPressed ? 0.7 : 1)
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
                CoverWash(show: show).frame(width: w, height: w)
                if w >= 56 {
                    CoverMotif(show: show).frame(width: w, height: w)
                        .opacity(w >= 96 ? 0.12 : 0.08)
                }
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
        .background(Theme.surface, in: RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: OpenAIKit.Radius.card, style: .continuous).strokeBorder(Theme.hairline))
        .accessibilityElement(children: .combine)
    }
}

extension View {
    /// White card with a hairline border.
    func card(padding: CGFloat = 16, radius: CGFloat = OpenAIKit.Radius.panel) -> some View {
        self.padding(padding)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: radius, style: .continuous).strokeBorder(Theme.hairline))
    }
}
