import AppKit
import ImageIO

// A deterministic constellation: stars alone trace the three strokes of a Z.
let side = 1024
let context = CGContext(data: nil, width: side, height: side, bitsPerComponent: 8, bytesPerRow: side * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
context.setFillColor(CGColor(red: 0.025, green: 0.105, blue: 0.12, alpha: 1))
context.fill(CGRect(x: 0, y: 0, width: side, height: side))
var seed: UInt64 = 1933
func unit() -> Double {
    seed = seed &* 6364136223846793005 &+ 1
    return Double(seed >> 33) / Double(UInt64(1) << 31)
}
func star(_ x: Double, _ y: Double, _ radius: Double, _ bright: Bool) {
    context.setFillColor(CGColor(red: 1, green: 0.92, blue: 0.73, alpha: bright ? 1 : 0.22))
    context.fillEllipse(in: CGRect(x: x-radius, y: y-radius, width: radius*2, height: radius*2))
    if bright && radius > 7 {
        for vertical in [false, true] {
            context.beginPath()
            let offsets: [(Double, Double)] = [(-3,0),(0,0.5),(3,0),(0,-0.5)]
            for (i, offset) in offsets.enumerated() {
                let p = CGPoint(x: x + (vertical ? offset.1 : offset.0)*radius, y: y + (vertical ? offset.0 : offset.1)*radius)
                if i == 0 { context.move(to: p) } else { context.addLine(to: p) }
            }
            context.closePath(); context.fillPath()
        }
    }
}
for _ in 0..<170 { star(unit()*1024, unit()*1024, 0.6+unit()*1.5, false) }
let points: [(Double, Double)] = [(240,760),(780,760),(240,264),(780,264)]
for (a,b) in [(0,1),(1,2),(2,3)] {
    for i in 0...12 {
        let t = Double(i)/12
        let x = points[a].0 + (points[b].0-points[a].0)*t
        let y = points[a].1 + (points[b].1-points[a].1)*t
        star(x,y,i % 3 == 0 ? 9 : 4,true)
        for _ in 0..<6 { star(x+(unit()-0.5)*28,y+(unit()-0.5)*28,1+unit()*2,true) }
    }
}
let destination = CGImageDestinationCreateWithURL(URL(fileURLWithPath: CommandLine.arguments[1]) as CFURL, "public.png" as CFString, 1, nil)!
CGImageDestinationAddImage(destination, context.makeImage()!, nil)
precondition(CGImageDestinationFinalize(destination))
