import SwiftUI

/// Host portrait from the asset catalog. Illustrations: DiceBear "Notionists" style (CC0),
/// generated with fixed options per host; see docs/DESIGN.md. Falls back to a symbol when
/// an asset is missing (the named Image renders nothing, revealing the symbol behind it).
struct HostAvatar: View {
    var host: Host
    var size: CGFloat = 48
    var body: some View {
        ZStack {
            Circle().fill(Theme.subtle)
            Image(systemName: "person.crop.circle.fill")
                .resizable().scaledToFit().foregroundStyle(Theme.hairline)
                .padding(size * 0.12)
            Image("host-\(host.id)").resizable().interpolation(.high).scaledToFill()
        }
        .frame(width: size, height: size).clipShape(Circle())
        .overlay(Circle().strokeBorder(Theme.hairline))
        .accessibilityHidden(true)
    }
}
