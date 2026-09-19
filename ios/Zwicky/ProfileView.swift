import SwiftUI

/// A local, anonymous profile avatar: a coloured disc with a chosen symbol or initials.
struct ProfileAvatar: View {
    var initials: String
    var symbol: String
    var hue: Double
    var size: CGFloat = 72

    var body: some View {
        ZStack {
            Circle().fill(LinearGradient(colors: [Color(hue: hue, saturation: 0.5, brightness: 0.95),
                                                  Color(hue: (hue + 0.09).truncatingRemainder(dividingBy: 1),
                                                        saturation: 0.62, brightness: 0.72)],
                                         startPoint: .topLeading, endPoint: .bottomTrailing))
            if symbol == "initials" {
                Text(initials.isEmpty ? "?" : initials)
                    .font(.system(size: size * 0.36, weight: .semibold, design: .rounded)).foregroundStyle(.white)
            } else {
                Image(systemName: symbol).font(.system(size: size * 0.4, weight: .medium)).foregroundStyle(.white)
            }
        }
        .frame(width: size, height: size)
        .overlay(Circle().strokeBorder(.white.opacity(0.22)))
        .accessibilityHidden(true)
    }
}

/// Edit the on-device profile. No account, no network; this is the anonymous
/// identity that a future Sign in with Apple upgrade can claim.
struct ProfileView: View {
    @EnvironmentObject var library: Library
    @EnvironmentObject var player: AudioPlayer
    @Environment(\.dismiss) var dismiss

    private let symbols = ["initials", "person.fill", "sparkles", "leaf", "waveform.path.ecg", "globe.americas",
                           "moon.stars", "atom", "cpu", "figure.run", "moon.zzz", "network",
                           "hexagon", "water.waves", "fossil.shell", "star", "flame"]
    private let hues: [Double] = [0.66, 0.58, 0.47, 0.36, 0.27, 0.14, 0.06, 0.82, 0.96]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    HStack(spacing: 16) {
                        ProfileAvatar(initials: library.initials, symbol: library.profileSymbol, hue: library.profileHue, size: 68)
                        VStack(alignment: .leading, spacing: 4) {
                            TextField("Display name", text: $library.profileName)
                                .font(.headline).textInputAutocapitalization(.words)
                            Text("Local profile · no account yet").font(.caption).foregroundStyle(Theme.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }

                Section("Avatar") {
                    LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 6), spacing: 12) {
                        ForEach(symbols, id: \.self) { name in
                            Button { library.profileSymbol = name } label: {
                                Group {
                                    if name == "initials" {
                                        Text("Aa").font(.subheadline.weight(.semibold))
                                    } else {
                                        Image(systemName: name).font(.title3)
                                    }
                                }
                                .frame(width: 40, height: 40)
                                .foregroundStyle(library.profileSymbol == name ? .white : Theme.ink)
                                .background(library.profileSymbol == name ? Theme.ink : Theme.subtle, in: Circle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel(name == "initials" ? "Initials" : name)
                        }
                    }
                    HStack(spacing: 12) {
                        ForEach(hues, id: \.self) { hue in
                            Button { library.profileHue = hue } label: {
                                Circle().fill(Color(hue: hue, saturation: 0.55, brightness: 0.9))
                                    .frame(width: 28, height: 28)
                                    .overlay(Circle().strokeBorder(Theme.ink, lineWidth: library.profileHue == hue ? 2.5 : 0))
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("Avatar colour")
                        }
                    }
                    .padding(.vertical, 2)
                }

                Section("Listening") {
                    LabeledContent("Total minutes", value: "\(player.totalMinutes)")
                    LabeledContent("Episodes finished", value: "\(library.history.count)")
                    LabeledContent("Streak", value: "\(player.streakDays) day\(player.streakDays == 1 ? "" : "s")")
                    LabeledContent("Following", value: "\(library.following.count) show\(library.following.count == 1 ? "" : "s")")
                    if let joined = library.joined {
                        LabeledContent("Listener since", value: joined.formatted(.dateTime.month(.abbreviated).year()))
                    }
                }

                Section {
                    Text("Your profile and listening data stay on this device. There is no account and no analytics SDK. Friends, sharing and social profiles are planned in docs/SOCIAL-PLAN.md.")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
            }
            .navigationTitle("Profile")
            .toolbar { Button("Done") { dismiss() } }
            .onAppear { library.ensureJoined() }
        }
    }
}
