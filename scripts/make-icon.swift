import AppKit
let side = 1024
let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: side, pixelsHigh: side, bitsPerSample: 8, samplesPerPixel: 3, hasAlpha: false, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
NSColor(red: 0.96, green: 0.95, blue: 0.91, alpha: 1).setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: side, height: side)).fill()
NSColor(red: 0.12, green: 0.14, blue: 0.13, alpha: 1).setFill()
NSBezierPath(ovalIn: NSRect(x: 248, y: 248, width: 528, height: 528)).fill()
NSColor(red: 0.12, green: 0.14, blue: 0.13, alpha: 0.75).setStroke()
let ring = NSBezierPath(ovalIn: NSRect(x: 90, y: 340, width: 844, height: 344))
ring.lineWidth = 12
let transform = AffineTransform(translationByX: 512, byY: 512)
var rotation = transform
rotation.rotate(byDegrees: 35)
rotation.translate(x: -512, y: -512)
ring.transform(using: rotation); ring.stroke()
NSColor(red: 0.88, green: 0.96, blue: 0.39, alpha: 1).setFill()
NSBezierPath(ovalIn: NSRect(x: 132, y: 213, width: 162, height: 162)).fill()
NSGraphicsContext.restoreGraphicsState()
let output = CommandLine.arguments[1]
try rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: output))
