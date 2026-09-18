import SwiftUI

/// Texture helpers for `ShowCover`: an organic colour wash, cached film grain and a
/// faint per-show line motif. SwiftUI + CoreGraphics only, so it also builds on macOS.
enum CoverTexture {
    // MARK: - Deterministic randomness

    /// SplitMix64: tiny, fast and identical on every launch and device.
    struct Random {
        private var state: UInt64
        init(seed: UInt64) { state = seed }
        mutating func next() -> UInt64 {
            state &+= 0x9E37_79B9_7F4A_7C15
            var z = state
            z = (z ^ (z >> 30)) &* 0xBF58_476D_1CE4_E5B9
            z = (z ^ (z >> 27)) &* 0x94D0_49BB_1331_11EB
            return z ^ (z >> 31)
        }
        /// Uniform in 0..<1.
        mutating func unit() -> Double { Double(next() >> 11) / Double(1 << 53) }
        mutating func range(_ r: ClosedRange<Double>) -> Double { r.lowerBound + unit() * (r.upperBound - r.lowerBound) }
    }

    /// FNV-1a — `String.hashValue` is randomised per launch, so it can't seed artwork.
    static func seed(_ string: String) -> UInt64 {
        string.utf8.reduce(0xCBF2_9CE4_8422_2325) { ($0 ^ UInt64($1)) &* 0x100_0000_01B3 }
    }

    // MARK: - Grain

    /// A 256px tile of soft grey noise centred on 50% grey, built once and shared by every
    /// cover. Drawn with `.overlay` blending, mid-grey is neutral so it only adds tooth.
    static let grain: CGImage? = {
        let side = 256
        var rng = Random(seed: 0x5EED_C0FE)
        var pixels = [UInt8](repeating: 128, count: side * side)
        for i in pixels.indices {
            // Sum of three uniforms ≈ gaussian: most grains are faint, a few are specks.
            let g = (rng.unit() + rng.unit() + rng.unit()) / 3 - 0.5
            pixels[i] = UInt8(clamping: Int((0.5 + g * 1.6) * 255))
        }
        guard let provider = CGDataProvider(data: Data(pixels) as CFData) else { return nil }
        return CGImage(width: side, height: side, bitsPerComponent: 8, bitsPerPixel: 8, bytesPerRow: side,
                       space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.none.rawValue),
                       provider: provider, decode: nil, shouldInterpolate: false, intent: .defaultIntent)
    }()

    // MARK: - Colour

    /// Linear interpolation between two colours (`Color.mix` is iOS 18+ only).
    static func mix(_ a: Color, _ b: Color, _ t: Double) -> Color {
        let env = EnvironmentValues()
        let x = a.resolve(in: env), y = b.resolve(in: env), f = Float(t)
        return Color(Color.Resolved(red: x.red + (y.red - x.red) * f, green: x.green + (y.green - x.green) * f,
                                    blue: x.blue + (y.blue - x.blue) * f, opacity: x.opacity + (y.opacity - x.opacity) * f))
    }
}

/// The cover's base colour: a 3×3 mesh on iOS 18, layered gradients on iOS 17.
/// Light pools top-right, deepens bottom-left, with a per-show wobble so the four
/// covers don't share one template.
struct CoverWash: View {
    var show: Show
    var body: some View {
        if #available(iOS 18, macOS 15, *) {
            MeshGradient(width: 3, height: 3, points: points, colors: colors, smoothsColors: true)
        } else {
            CoverWashFallback(show: show)
        }
    }

    private var colors: [Color] {
        let m = CoverTexture.mix
        return [
            m(show.mid, show.dark, 0.15), m(show.mid, show.light, 0.55), m(show.light, .white, 0.22),
            m(show.mid, show.dark, 0.5), show.mid, show.light,
            show.dark, m(show.dark, show.mid, 0.35), m(show.mid, show.light, 0.15),
        ]
    }

    private var points: [SIMD2<Float>] {
        var rng = CoverTexture.Random(seed: CoverTexture.seed(show.id))
        func j(_ amount: Double) -> Float { Float(rng.range(-amount...amount)) }
        return [
            [0, 0], [0.5 + j(0.15), 0], [1, 0],
            [0, 0.5 + j(0.15)], [0.5 + j(0.14), 0.48 + j(0.14)], [1, 0.5 + j(0.15)],
            [0, 1], [0.5 + j(0.15), 1], [1, 1],
        ]
    }
}

/// iOS 17 approximation of the mesh: a diagonal wash with offset pools of light and shade.
struct CoverWashFallback: View {
    var show: Show
    var body: some View {
        GeometryReader { geometry in
            let w = geometry.size.width
            var rng = CoverTexture.Random(seed: CoverTexture.seed(show.id))
            let pool = UnitPoint(x: 0.42 + rng.range(-0.12...0.12), y: 0.5 + rng.range(-0.12...0.12))
            ZStack {
                LinearGradient(colors: [show.light, show.mid, show.dark], startPoint: .topTrailing, endPoint: .bottomLeading)
                RadialGradient(colors: [show.mid.opacity(0.85), .clear], center: pool, startRadius: 0, endRadius: w * 0.5)
                RadialGradient(colors: [CoverTexture.mix(show.light, .white, 0.22).opacity(0.9), .clear],
                               center: UnitPoint(x: 0.95, y: 0.05), startRadius: 0, endRadius: w * 0.55)
                RadialGradient(colors: [show.dark.opacity(0.9), .clear], center: UnitPoint(x: 0.05, y: 0.98),
                               startRadius: 0, endRadius: w * 0.6)
                RadialGradient(colors: [show.light.opacity(0.35), .clear], center: UnitPoint(x: 1, y: 0.95),
                               startRadius: 0, endRadius: w * 0.45)
            }
        }
    }
}

/// Film grain over the whole cover. Blend it inside the cover's compositing group.
struct CoverGrain: View {
    var body: some View {
        if let grain = CoverTexture.grain {
            // Scale 2: one grain is half a point, fine enough to read as print, not pixels.
            Image(decorative: grain, scale: 2).resizable(resizingMode: .tile)
        }
    }
}

/// A faint abstract line pattern, different for each show. Strokes only, no symbols.
struct CoverMotif: View {
    var show: Show
    var body: some View {
        Canvas { context, size in
            let w = size.width
            let line = max(0.5, w * 0.0045)
            var rng = CoverTexture.Random(seed: CoverTexture.seed(show.id) ^ 0xA5A5)
            switch show.id {
            case "nova": // The Long View: tilted orbits around a point off the top-right corner
                let centre = CGPoint(x: w * 0.92, y: w * 0.08)
                context.translateBy(x: centre.x, y: centre.y)
                context.rotate(by: .degrees(-28))
                for i in 1...7 {
                    let r = w * (0.18 + Double(i) * 0.14)
                    context.stroke(Path(ellipseIn: CGRect(x: -r, y: -r * 0.62, width: r * 2, height: r * 1.24)),
                                   with: .color(.white), lineWidth: line)
                }
                let r = w * 0.74, a = 2.35
                context.fill(Path(ellipseIn: CGRect(x: cos(a) * r - line * 2.5, y: sin(a) * r * 0.62 - line * 2.5,
                                                    width: line * 5, height: line * 5)), with: .color(.white))
            case "fern": // Wild Company: flowing, slightly uneven growth lines
                for i in 0..<11 {
                    let y0 = w * (-0.1 + Double(i) * 0.12)
                    let wobble = rng.range(0.03...0.07)
                    var path = Path()
                    path.move(to: CGPoint(x: -w * 0.05, y: y0 + w * 0.25))
                    path.addCurve(to: CGPoint(x: w * 1.05, y: y0 - w * 0.1),
                                  control1: CGPoint(x: w * 0.35, y: y0 + w * (0.1 + wobble * 3)),
                                  control2: CGPoint(x: w * 0.65, y: y0 - w * (0.2 + wobble)))
                    context.stroke(path, with: .color(.white), lineWidth: line)
                }
            case "ada": // Signal & Noise: a fine, enveloped waveform band
                for k in 0..<4 {
                    var path = Path()
                    let base = w * (0.34 + Double(k) * 0.035)
                    let phase = Double(k) * 0.6
                    for step in 0...160 {
                        let t = Double(step) / 160
                        let envelope = pow(sin(.pi * t), 2)
                        let y = base + envelope * w * 0.06 * (sin(t * 30 + phase) * 0.8 + sin(t * 53 + phase * 2) * 0.2)
                        let p = CGPoint(x: t * w, y: y)
                        if step == 0 { path.move(to: p) } else { path.addLine(to: p) }
                    }
                    context.stroke(path, with: .color(.white.opacity(1 - Double(k) * 0.15)), lineWidth: line)
                }
            default: // Common Ground: nested topographic rings, irregular like real contours
                let centre = CGPoint(x: w * 0.72, y: w * 0.38)
                let lobes = (0..<4).map { _ in (rng.range(0.05...0.12), rng.range(0...(2 * .pi))) }
                for i in 1...9 {
                    let r = w * Double(i) * 0.085
                    var path = Path()
                    for step in 0...90 {
                        let a = Double(step) / 90 * 2 * .pi
                        var k = 1.0
                        for (n, lobe) in lobes.enumerated() { k += lobe.0 * sin(a * Double(n + 2) + lobe.1 + Double(i) * 0.25) }
                        let p = CGPoint(x: centre.x + cos(a) * r * k, y: centre.y + sin(a) * r * k * 0.9)
                        if step == 0 { path.move(to: p) } else { path.addLine(to: p) }
                    }
                    path.closeSubpath()
                    context.stroke(path, with: .color(.white), lineWidth: line)
                }
            }
        }
    }
}
