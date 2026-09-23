import Foundation

/// Pure listening maths, kept free of AVFoundation so it can be unit tested headlessly.
enum ListeningMath {
    static func progress(position: Double, duration: Double, completed: Bool) -> Double {
        if completed { return 1 }
        guard position.isFinite, duration > 0 else { return 0 }
        return min(0.99, max(0, position / duration))
    }

    static func minutesLeft(progress: Double, duration: Double) -> Int {
        max(1, Int(((1 - progress) * duration / 60).rounded()))
    }

    static func minutes(seconds: Double) -> Int { Int((seconds / 60).rounded()) }

    /// Consecutive days ending today (or yesterday, if today is still quiet) with at least a minute.
    static func streak(seconds: [String: Double], today: Date, calendar: Calendar = .current,
                       key: (Date) -> String) -> Int {
        var count = 0
        var day = calendar.startOfDay(for: today)
        if (seconds[key(day)] ?? 0) < 60 { day = calendar.date(byAdding: .day, value: -1, to: day)! }
        while (seconds[key(day)] ?? 0) >= 60 {
            count += 1
            day = calendar.date(byAdding: .day, value: -1, to: day)!
        }
        return count
    }
}

/// Ignore tiny or invalid player-time changes before updating the visible clock.
enum PlaybackTickPolicy {
    static func shouldPublish(current: Double, next: Double) -> Bool {
        next.isFinite && (!current.isFinite || abs(current - next) > 0.05)
    }

    static func listenedInterval(since last: Date?, now: Date) -> Double {
        guard let last else { return 0 }
        return min(max(now.timeIntervalSince(last), 0), 0.5)
    }

    /// The system advances lock-screen elapsed time at the advertised playback rate.
    /// Reconcile occasionally to correct drift without rebuilding metadata each second.
    static func shouldSyncNowPlaying(last: Double?, next: Double, interval: Double = 10) -> Bool {
        guard next.isFinite else { return false }
        guard let last, last.isFinite else { return true }
        return abs(next - last) >= interval
    }
}

/// Device-local listening state, independent of audio and view lifecycles.
struct ListeningState: Codable {
    var currentID: String?
    var queue: [String] = []
    var positions: [String: Double] = [:]
    var completed: Set<String> = []
    mutating func enqueue(_ id: String) {
        guard id != currentID, !queue.contains(id) else { return }
        queue.append(id)
    }
    mutating func begin(_ id: String) { currentID = id; queue.removeAll { $0 == id }; completed.remove(id) }
    mutating func checkpoint(_ seconds: Double) {
        guard let id = currentID, seconds.isFinite, seconds >= 0 else { return }
        positions[id] = seconds
    }
    mutating func finish() {
        if let id = currentID { completed.insert(id); positions.removeValue(forKey: id) }
    }
    mutating func next() -> String? { queue.isEmpty ? nil : queue.removeFirst() }
    mutating func move(_ id: String, by offset: Int) {
        guard let index = queue.firstIndex(of: id), queue.indices.contains(index + offset) else { return }
        queue.swapAt(index, index + offset)
    }
}
