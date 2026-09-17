import SwiftUI

/// Host portrait from the asset catalog. Illustrations: DiceBear "Notionists" style (CC0),
/// generated with fixed options per host; see docs/DESIGN.md.
struct HostAvatar: View {
    var host: Host
    var size: CGFloat = 48
    var body: some View {
        Image("host-\(host.id)").resizable().interpolation(.high).scaledToFill()
            .frame(width: size, height: size).clipShape(Circle())
            .overlay(Circle().strokeBorder(Theme.hairline))
            .accessibilityHidden(true)
    }
}
