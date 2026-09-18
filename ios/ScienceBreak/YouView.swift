import Charts
import SwiftUI

/// Personal listening: today's goal, the week, totals, followed shows and settings.
struct YouView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @State private var settings = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    /// What the ring and the minutes label currently show; animated toward the real values.
    @State private var shownProgress: Double = 0
    @State private var shownMinutes = 0
    /// Drives the brief celebratory pulse when the goal is met.
    @State private var celebrating = false

    private var followed: [Show] { Show.all.filter { library.isFollowing($0) } }
    private var finished: [Story] { library.latest.filter { player.progress(of: $0) >= 1 } }
    private var goalProgress: Double { min(1, Double(player.minutesToday) / Double(max(library.dailyGoalMinutes, 1))) }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    goalCard
                    weekCard
                    totals
                    followingSection
                    VStack(alignment: .leading, spacing: 12) {
                        SectionHeader(title: "Settings")
                        Button { settings = true } label: {
                            row("gearshape", "App settings", "Feed, privacy, credits")
                        }.buttonStyle(PressableStyle(scale: 0.98))
                        NavigationLink { QueueView() } label: {
                            row("list.bullet", "Up next", "\(player.queuedStories.count) episode\(player.queuedStories.count == 1 ? "" : "s") queued")
                        }.buttonStyle(PressableStyle(scale: 0.98))
                    }
                    Text("Listening data stays on this device. There is no account and no analytics SDK.")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
                .padding(.horizontal, 20).padding(.bottom, 24)
            }
            .background(Theme.canvas)
            .navigationTitle("You")
            .sheet(isPresented: $settings) { SettingsView() }
        }
    }

    private var goalCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .center, spacing: 18) {
                ZStack {
                    Circle().stroke(Theme.subtle, lineWidth: 10)
                    Circle().trim(from: 0, to: shownProgress)
                        .stroke(AngularGradient(colors: Show.all.map(\.mid) + [Show.all[0].mid], center: .center),
                                style: StrokeStyle(lineWidth: 10, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .shadow(color: Show.all[0].mid.opacity(celebrating ? 0.55 : 0), radius: celebrating ? 12 : 0)
                    VStack(spacing: 0) {
                        Text("\(shownMinutes)").font(.system(size: 24, weight: .semibold, design: .rounded)).monospacedDigit()
                            .contentTransition(.numericText(value: Double(shownMinutes)))
                        Text("min").font(.caption2).foregroundStyle(Theme.secondary)
                    }
                }
                .frame(width: 92, height: 92)
                .scaleEffect(celebrating ? 1.08 : 1)
                .onAppear { syncRing() }
                .onChange(of: goalProgress) { old, new in
                    syncRing()
                    if old < 1, new >= 1 { celebrate() }
                }
                .onChange(of: player.minutesToday) { _, _ in syncRing() }
                .accessibilityElement(children: .ignore)
                .accessibilityLabel("\(player.minutesToday) of \(library.dailyGoalMinutes) minutes listened today")
                VStack(alignment: .leading, spacing: 6) {
                    Text("Today's goal").font(.headline)
                    Text(goalProgress >= 1 ? "Goal met. Anything more is a bonus." : "\(max(0, library.dailyGoalMinutes - player.minutesToday)) min to go — about \(max(1, Int((Double(max(0, library.dailyGoalMinutes - player.minutesToday)) / 3).rounded(.up)))) episode\(max(0, library.dailyGoalMinutes - player.minutesToday) > 3 ? "s" : "").")
                        .font(.subheadline).foregroundStyle(Theme.secondary)
                    if player.streakDays > 0 {
                        Label("\(player.streakDays) day streak", systemImage: "flame").font(.caption.weight(.medium)).foregroundStyle(Theme.ink)
                    }
                }
                Spacer(minLength: 0)
            }
            Divider().overlay(Theme.hairline)
            HStack {
                Text("Daily goal").font(.subheadline)
                Spacer()
                Stepper("\(library.dailyGoalMinutes) min", value: $library.dailyGoalMinutes, in: 3...60, step: 1)
                    .labelsHidden().fixedSize()
                    .onChange(of: library.dailyGoalMinutes) { _, _ in Haptics.selection() }
                Text("\(library.dailyGoalMinutes) min").font(.subheadline.weight(.semibold)).monospacedDigit().frame(width: 58, alignment: .trailing)
                    .contentTransition(.numericText(value: Double(library.dailyGoalMinutes)))
                    .animation(Motion.standard(reduceMotion: reduceMotion), value: library.dailyGoalMinutes)
            }
        }
        .card()
    }

    /// Moves the ring fill and minutes label to the current values.
    private func syncRing() {
        withAnimation(reduceMotion ? .easeInOut(duration: 0.35) : .spring(response: 0.9, dampingFraction: 0.85)) {
            shownProgress = goalProgress
            shownMinutes = player.minutesToday
        }
    }

    /// Success haptic plus, unless Reduce Motion is on, a short scale-and-glow pulse on the ring.
    private func celebrate() {
        Haptics.success()
        guard !reduceMotion else { return }
        withAnimation(.spring(response: 0.3, dampingFraction: 0.5)) { celebrating = true }
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(450))
            withAnimation(Motion.spring) { celebrating = false }
        }
    }

    private var weekCard: some View {
        VStack(alignment: .leading, spacing: 14) {
            SectionHeader(title: "This week") { Text("\(player.minutesThisWeek) min") }
            Chart(player.week, id: \.day) { entry in
                BarMark(
                    x: .value("Day", entry.day, unit: .day),
                    y: .value("Minutes", entry.minutes),
                    width: .fixed(18)
                )
                .foregroundStyle(Calendar.current.isDateInToday(entry.day) ? Theme.ink : Theme.ink.opacity(0.28))
                .cornerRadius(5)
            }
            .chartYAxis { AxisMarks(position: .leading, values: .automatic(desiredCount: 3)) }
            .chartXAxis { AxisMarks(values: .stride(by: .day)) { value in
                AxisValueLabel(format: .dateTime.weekday(.narrow))
            } }
            .frame(height: 140)
            .accessibilityLabel("Minutes listened each day this week")
            if player.minutesThisWeek == 0 {
                Text("No listening logged yet. Minutes appear here as you play episodes.").font(.caption).foregroundStyle(Theme.secondary)
            }
        }
        .card()
    }

    private var totals: some View {
        HStack(alignment: .top, spacing: 10) {
            StatTile(value: "\(finished.count)", label: "finished", symbol: "checkmark.circle")
            StatTile(value: "\(library.saved.count)", label: "saved", symbol: "bookmark")
            StatTile(value: "\(sourcesCount)", label: "sources", symbol: "link")
        }
        // StatTile's number Text picks this up from the environment.
        .contentTransition(.numericText())
        .animation(Motion.standard(reduceMotion: reduceMotion), value: [finished.count, library.saved.count, sourcesCount])
    }

    private var sourcesCount: Int {
        Set(finished.flatMap { $0.sources.map(\.url) }).count
    }

    private var followingSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeader(title: "Following") { Text("\(followed.count) of \(Show.all.count)") }
            ForEach(Show.all) { show in
                HStack(spacing: 12) {
                    ShowCover(show: show).frame(width: 44)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(show.title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
                        Text(show.host.name).font(.caption).foregroundStyle(Theme.secondary)
                    }
                    Spacer()
                    Button { Haptics.selection(); library.toggleFollow(show) } label: {
                        Text(library.isFollowing(show) ? "Following" : "Follow")
                            .font(.caption.weight(.semibold)).padding(.horizontal, 14).frame(height: 32)
                            .foregroundStyle(library.isFollowing(show) ? Theme.ink : .white)
                            .background(library.isFollowing(show) ? Theme.surface : Theme.ink, in: Capsule())
                            .overlay(Capsule().strokeBorder(library.isFollowing(show) ? Theme.hairline : .clear))
                    }
                    .buttonStyle(.pressable)
                    .animation(Motion.standard(reduceMotion: reduceMotion), value: library.isFollowing(show))
                    .accessibilityLabel(library.isFollowing(show) ? "Unfollow \(show.title)" : "Follow \(show.title)")
                }
                .padding(.vertical, 6)
            }
        }
    }

    private func row(_ symbol: String, _ title: String, _ subtitle: String) -> some View {
        HStack(spacing: 14) {
            Image(systemName: symbol).font(.body.weight(.medium)).foregroundStyle(Theme.ink)
                .frame(width: 36, height: 36).background(Theme.subtle, in: Circle())
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.subheadline.weight(.semibold)).foregroundStyle(Theme.ink)
                Text(subtitle).font(.caption).foregroundStyle(Theme.secondary)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.caption.weight(.semibold)).foregroundStyle(Theme.tertiary)
        }
        .card(padding: 14, radius: OpenAIKit.Radius.card)
    }
}
