import Foundation
import OSLog

/// Performance logging and signposts.
///
/// Everything is tagged with the bundle id as the subsystem, so a single filter shows
/// the whole app:
///
///   Console.app         subsystem: com.xmevans10.Zwicky   (or category: perf)
///   Instruments         Points of Interest (os_signpost) for the same subsystem
///   Terminal on device  log stream --predicate 'subsystem == "com.xmevans10.Zwicky"'
///
/// `Logger` and `OSSignposter` are cheap in Release: strings are not built unless a log
/// tool is attached, so these calls can stay in shipped builds.
enum Telemetry {
    static let subsystem = Bundle.main.bundleIdentifier ?? "com.xmevans10.Zwicky"

    static let app = Logger(subsystem: subsystem, category: "app")
    static let feed = Logger(subsystem: subsystem, category: "feed")
    static let audio = Logger(subsystem: subsystem, category: "audio")
    static let perf = Logger(subsystem: subsystem, category: "perf")

    private static let signposter = OSSignposter(subsystem: subsystem, category: "perf")

    /// Monotonic clock reading for manual elapsed-time measurements.
    static func now() -> UInt64 { DispatchTime.now().uptimeNanoseconds }

    /// Milliseconds elapsed since a `now()` reading.
    static func ms(since start: UInt64) -> Double {
        Double(DispatchTime.now().uptimeNanoseconds &- start) / 1_000_000
    }

    /// Time a synchronous block: a signpost interval plus a `perf` log line.
    @discardableResult
    static func measure<T>(_ name: StaticString, _ body: () throws -> T) rethrows -> T {
        let label = String(describing: name)
        let state = signposter.beginInterval(name)
        let start = now()
        defer {
            let elapsed = ms(since: start)
            signposter.endInterval(name, state)
            perf.debug("\(label, privacy: .public) \(elapsed, format: .fixed(precision: 1)) ms")
        }
        return try body()
    }

    /// Time an async block: a signpost interval plus a `perf` log line.
    @discardableResult
    static func measure<T>(_ name: StaticString, _ body: () async throws -> T) async rethrows -> T {
        let label = String(describing: name)
        let state = signposter.beginInterval(name)
        let start = now()
        defer {
            let elapsed = ms(since: start)
            signposter.endInterval(name, state)
            perf.debug("\(label, privacy: .public) \(elapsed, format: .fixed(precision: 1)) ms")
        }
        return try await body()
    }
}
