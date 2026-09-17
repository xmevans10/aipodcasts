import Foundation

@main struct ListeningStateChecks {
    static func main() throws {
        var state = ListeningState()
        state.begin("a")
        state.enqueue("a"); state.enqueue("b"); state.enqueue("b"); state.enqueue("c")
        assert(state.queue == ["b", "c"], "Exclude current item and duplicates")
        state.move("b", by: -1)
        assert(state.queue == ["b", "c"], "Ignore out-of-bounds movement")
        state.move("c", by: -1)
        assert(state.queue == ["c", "b"])
        state.checkpoint(42); state.checkpoint(.nan); state.checkpoint(-1)
        assert(state.positions["a"] == 42, "Invalid progress cannot corrupt resume")
        let restored = try JSONDecoder().decode(ListeningState.self, from: JSONEncoder().encode(state))
        assert(restored.queue == state.queue && restored.positions == state.positions && restored.currentID == "a")
        state.finish()
        assert(state.completed.contains("a") && state.positions["a"] == nil)
        let next = state.next()
        assert(next == "c")
        state.begin(next!)
        assert(state.currentID == "c" && state.queue == ["b"])
        state.begin("a")
        assert(!state.completed.contains("a"), "Replay clears completion")
        assert(state.next() == "b" && state.next() == nil)
        print("Listening state checks passed: queue, ordering, resume, persistence, completion, replay")
    }
}
