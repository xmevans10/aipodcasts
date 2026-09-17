import SwiftUI

enum ScienceBreak {
    static let paper = Color(red: 0.96, green: 0.95, blue: 0.91)
    static let ink = Color(red: 0.12, green: 0.14, blue: 0.13)
    static let acid = Color(red: 0.88, green: 0.96, blue: 0.39)
    static let muted = Color(red: 0.39, green: 0.41, blue: 0.38)
}
struct CapsuleButton: ButtonStyle {
    var light = false
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.font(.system(.subheadline, design: .rounded, weight: .semibold))
            .padding(.horizontal, 22).padding(.vertical, 16)
            .foregroundStyle(light ? ScienceBreak.ink : ScienceBreak.paper)
            .background(light ? ScienceBreak.acid : ScienceBreak.ink, in: Capsule())
            .opacity(configuration.isPressed ? 0.7 : 1)
    }
}
struct Eyebrow: View {
    var text: String
    var body: some View { Text(text).font(.system(size: 10, weight: .bold, design: .monospaced)).tracking(2).foregroundStyle(ScienceBreak.muted) }
}
struct OrbitalArt: View {
    var hue: Double = 0.66
    var body: some View {
        GeometryReader { g in
            let w = g.size.width
            ZStack {
                Color(hue: hue, saturation: 0.2, brightness: 0.84)
                ForEach(0..<7) { i in
                    Ellipse().stroke(ScienceBreak.ink.opacity(0.22), lineWidth: 0.7)
                        .frame(width: w * (0.5 + Double(i) * 0.12), height: w * (0.25 + Double(i) * 0.045))
                        .rotationEffect(.degrees(-34)).offset(x: w * 0.13, y: -8)
                }
                Circle().fill(RadialGradient(colors: [ScienceBreak.paper, Color(hue: hue, saturation: 0.25, brightness: 0.68), ScienceBreak.ink], center: .topLeading, startRadius: 0, endRadius: w * 0.5))
                    .frame(width: w * 0.43, height: w * 0.43).offset(x: w * 0.1, y: -5)
                Circle().fill(ScienceBreak.acid).frame(width: w * 0.1, height: w * 0.1).offset(x: -w * 0.24, y: w * 0.12)
                Image(systemName: "sparkle").font(.system(size: 23, weight: .ultraLight)).offset(x: -w * 0.29, y: -w * 0.17)
                VStack { HStack { Text("FIELD NOTES / \(hue == 0.66 ? "001" : "002")"); Spacer(); Image(systemName: "viewfinder") }; Spacer() }
                    .font(.system(size: 8, weight: .medium, design: .monospaced)).tracking(2).padding(20)
            }.clipped()
        }.accessibilityHidden(true)
    }
}
struct HostAvatar: View {
    var host: Host
    var size: CGFloat = 48
    var body: some View {
        ZStack {
            Circle().fill(host.color)
            Image(systemName: host.symbol).font(.system(size: size * 0.4, weight: .light)).foregroundStyle(ScienceBreak.ink)
        }.frame(width: size, height: size).accessibilityHidden(true)
    }
}
struct StoryRow: View {
    var story: Story
    var body: some View {
        HStack(spacing: 15) {
            OrbitalArt(hue: story.host.hue).frame(width: 80, height: 88).clipShape(RoundedRectangle(cornerRadius: 15))
            VStack(alignment: .leading, spacing: 7) {
                Eyebrow(text: "\(story.topic) · \(story.minutes) MIN")
                Text(story.title).font(.system(.headline, design: .serif)).multilineTextAlignment(.leading)
                Text("with \(story.host.name)").font(.caption).foregroundStyle(ScienceBreak.muted)
            }
            Spacer(minLength: 0)
            Image(systemName: "arrow.up.right").font(.caption)
        }.foregroundStyle(ScienceBreak.ink).padding(.vertical, 9)
    }
}
