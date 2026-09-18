import SwiftUI

/// Native adaptation of OpenAI Apps SDK UI semantic tokens (MIT).
/// Upstream commit and full license are recorded in docs/DESIGN.md.
/// Web rem units map to points; interactive targets use iOS's 44pt minimum.
enum OpenAIKit {
    enum Radius {
        static let small: CGFloat = 6
        static let medium: CGFloat = 8
        static let large: CGFloat = 12
        static let card: CGFloat = 16
        static let panel: CGFloat = 20
        static let hero: CGFloat = 24
    }
    static let spacing: CGFloat = 4
    static let minimumTarget: CGFloat = 44
    static let neutral900 = Color(red: 24 / 255, green: 24 / 255, blue: 24 / 255)
    static let neutral100 = Color(red: 237 / 255, green: 237 / 255, blue: 237 / 255)
}
