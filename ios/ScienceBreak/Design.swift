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
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.subheadline.weight(.semibold))
            .padding(.horizontal, 20).frame(minHeight: 46).frame(maxWidth: fullWidth ? .infinity : nil)
            .foregroundStyle(.white).background(Theme.ink, in: Capsule())
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

/// Podcast cover art: the show's gradient, a large symbol and the title set in serif.
/// Size it with `.frame(width:)`; it stays square.
struct ShowCover: View {
    var show: Show
    var body: some View {
        GeometryReader { geometry in
            let w = geometry.size.width
            ZStack(alignment: .bottomLeading) {
                LinearGradient(colors: [show.light, show.dark], startPoint: .topTrailing, endPoint: .bottomLeading)
                if w >= 96 {
                    Image(systemName: show.symbol).font(.system(size: w * 0.5, weight: .thin)).foregroundStyle(.white.opacity(0.2))
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing).offset(x: w * 0.06, y: -w * 0.04)
                    VStack(alignment: .leading, spacing: w * 0.025) {
                        Text(show.title).font(.system(size: w * 0.125, weight: .semibold, design: .serif)).tracking(-0.2)
                            .lineLimit(2).minimumScaleFactor(0.8)
                        Text(show.host.name.uppercased()).font(.system(size: max(7, w * 0.048), weight: .semibold)).tracking(0.8).opacity(0.82)
                    }.foregroundStyle(.white).padding(w * 0.085)
                } else {
                    Image(systemName: show.symbol).font(.system(size: w * 0.42, weight: .regular)).foregroundStyle(.white)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: max(6, w * 0.11), style: .continuous))
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
            Text(label).font(.caption).foregroundStyle(Theme.secondary).lineLimit(2, reservesSpace: true)
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
