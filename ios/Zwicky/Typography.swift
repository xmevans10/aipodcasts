import SwiftUI

/// A deliberate type scale with real contrast: a big serif hero down to a tracked overline.
/// Every step scales with Dynamic Type via `@ScaledMetric`, anchored to a system text style.
///
/// Scale (at the default content size):
///   hero 42 · largeTitle 40 · title 26 · numeral 40 (rounded) · headline 17 · body 15 · meta 13 · overline 11
extension Theme {
    struct TypeStyle {
        var size: CGFloat
        var weight: Font.Weight
        var design: Font.Design = .default
        var relativeTo: Font.TextStyle
        /// Letter spacing in points at the default size; scales with the font.
        var tracking: CGFloat = 0
        var uppercase = false
        var monospacedDigits = false
    }
}

/// The steps of the scale, so call sites read `.typeStyle(.hero)`.
extension Theme.TypeStyle {
    /// Featured-episode titles: the one thing on screen that shouts.
    static let hero = Theme.TypeStyle(size: 42, weight: .bold, design: .serif, relativeTo: .largeTitle, tracking: -1.2)
    /// Screen greetings and page titles.
    static let largeTitle = Theme.TypeStyle(size: 40, weight: .semibold, design: .serif, relativeTo: .largeTitle, tracking: -1.0)
    /// Section headers.
    static let title = Theme.TypeStyle(size: 26, weight: .semibold, design: .serif, relativeTo: .title, tracking: -0.5)
    /// Card and row titles.
    static let headline = Theme.TypeStyle(size: 17, weight: .semibold, relativeTo: .headline, tracking: -0.2)
    /// Running copy and deks.
    static let body = Theme.TypeStyle(size: 15, weight: .regular, relativeTo: .body)
    /// Quiet metadata: dates, durations, captions.
    static let meta = Theme.TypeStyle(size: 13, weight: .regular, relativeTo: .footnote)
    /// Small-caps style label above a title.
    static let overline = Theme.TypeStyle(size: 11, weight: .semibold, relativeTo: .caption2, tracking: 1.5, uppercase: true)
    /// Big rounded figures for stats.
    static let numeral = Theme.TypeStyle(size: 40, weight: .bold, design: .rounded, relativeTo: .largeTitle, tracking: -0.8, monospacedDigits: true)
}

private struct ThemeTypeModifier: ViewModifier {
    let style: Theme.TypeStyle
    @ScaledMetric private var size: CGFloat

    init(_ style: Theme.TypeStyle) {
        self.style = style
        _size = ScaledMetric(wrappedValue: style.size, relativeTo: style.relativeTo)
    }

    func body(content: Content) -> some View {
        let scale = size / style.size
        var font = Font.system(size: size, weight: style.weight, design: style.design)
        if style.monospacedDigits { font = font.monospacedDigit() }
        return content
            .font(font)
            .tracking(style.tracking * scale)
            .textCase(style.uppercase ? .uppercase : nil)
    }
}

extension View {
    /// Applies a step of the app's type scale (font, tracking, case), scaled for Dynamic Type.
    func typeStyle(_ style: Theme.TypeStyle) -> some View { modifier(ThemeTypeModifier(style)) }
}
