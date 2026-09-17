import Foundation

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
