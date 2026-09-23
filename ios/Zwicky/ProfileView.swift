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

    private enum ProfileField: Hashable { case name, bio }
    @FocusState private var focusedField: ProfileField?

    private struct AvatarChoice: Identifiable {
        let id: String
        let name: String
    }

    private struct ColorChoice: Identifiable {
        let id: String
        let hue: Double
    }

    private let symbols: [AvatarChoice] = [
        .init(id: "initials", name: "Initials"), .init(id: "person.fill", name: "Person"),
        .init(id: "sparkles", name: "Sparkles"), .init(id: "leaf", name: "Leaf"),
        .init(id: "waveform.path.ecg", name: "Waveform"), .init(id: "globe.americas", name: "Globe"),
        .init(id: "moon.stars", name: "Moon and stars"), .init(id: "atom", name: "Atom"),
        .init(id: "cpu", name: "Computer chip"), .init(id: "figure.run", name: "Runner"),
        .init(id: "moon.zzz", name: "Sleeping moon"), .init(id: "network", name: "Network"),
        .init(id: "hexagon", name: "Hexagon"), .init(id: "water.waves", name: "Waves"),
        .init(id: "fossil.shell", name: "Shell"), .init(id: "star", name: "Star"),
        .init(id: "flame", name: "Flame")
    ]
    private let colors: [ColorChoice] = [
        .init(id: "Indigo", hue: 0.66), .init(id: "Blue", hue: 0.58),
        .init(id: "Teal", hue: 0.47), .init(id: "Green", hue: 0.36),
        .init(id: "Lime", hue: 0.27), .init(id: "Gold", hue: 0.14),
        .init(id: "Orange", hue: 0.06), .init(id: "Purple", hue: 0.82),
        .init(id: "Pink", hue: 0.96)
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    HStack(spacing: 16) {
                        ProfileAvatar(initials: library.initials, symbol: library.profileSymbol, hue: library.profileHue, size: 68)
                        VStack(alignment: .leading, spacing: 4) {
                            TextField("Display name", text: $library.profileName)
                                .font(.headline).textInputAutocapitalization(.words)
                                .focused($focusedField, equals: .name)
                                .submitLabel(.done)
                                .onSubmit(normalizeProfile)
                                .onChange(of: library.profileName) { _, value in
                                    if value.count > 40 { library.profileName = String(value.prefix(40)) }
                                }
                            Text("Your private profile on this device").font(.caption).foregroundStyle(Theme.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                    TextField("A little about you", text: $library.profileBio, axis: .vertical)
                        .lineLimit(2...4)
                        .focused($focusedField, equals: .bio)
                        .onChange(of: library.profileBio) { _, value in
                            if value.count > 160 { library.profileBio = String(value.prefix(160)) }
                        }
                    Text("\(library.profileBio.count) of 160 characters")
                        .font(.caption2).foregroundStyle(Theme.secondary)
                        .accessibilityLabel("Biography, \(160 - library.profileBio.count) characters remaining")
                    Picker("Favorite show", selection: $library.favoriteShowID) {
                        Text("None").tag("")
                        ForEach(Show.all) { show in Text(show.title).tag(show.id) }
                    }
                }

                Section("Avatar") {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 44), spacing: 12)], spacing: 12) {
                        ForEach(symbols) { choice in
                            Button { library.profileSymbol = choice.id } label: {
                                Group {
                                    if choice.id == "initials" {
                                        Text("Aa").font(.subheadline.weight(.semibold))
                                    } else {
                                        Image(systemName: choice.id).font(.title3)
                                    }
                                }
                                .frame(width: 44, height: 44)
                                .foregroundStyle(library.profileSymbol == choice.id ? .white : Theme.ink)
                                .background(library.profileSymbol == choice.id ? Theme.ink : Theme.subtle, in: Circle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel(choice.name)
                            .accessibilityAddTraits(library.profileSymbol == choice.id ? .isSelected : [])
                        }
                    }
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 44), spacing: 12)], spacing: 12) {
                        ForEach(colors) { choice in
                            Button { library.profileHue = choice.hue } label: {
                                Circle().fill(Color(hue: choice.hue, saturation: 0.55, brightness: 0.9))
                                    .frame(width: 44, height: 44)
                                    .overlay(Circle().strokeBorder(Theme.ink, lineWidth: library.profileHue == choice.hue ? 3 : 0))
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel("\(choice.id) avatar color")
                            .accessibilityAddTraits(library.profileHue == choice.hue ? .isSelected : [])
                        }
                    }
                    .padding(.vertical, 2)
                }

                Section("Listening") {
                    LabeledContent("Total minutes", value: "\(player.totalMinutes)")
                    LabeledContent("Episodes finished", value: "\(player.listening.completed.count)")
                    LabeledContent("Streak", value: "\(player.streakDays) day\(player.streakDays == 1 ? "" : "s")")
                    LabeledContent("Following", value: "\(library.following.count) show\(library.following.count == 1 ? "" : "s")")
                    if let joined = library.joined {
                        LabeledContent("Listener since", value: joined.formatted(.dateTime.month(.abbreviated).year()))
                    }
                }

                Section {
                    Text("Your profile and listening data stay on this device. You can share episodes without an account.")
                        .font(.caption).foregroundStyle(Theme.secondary)
                }
            }
            .navigationTitle("Profile")
            .toolbar { Button("Done") { normalizeProfile(); dismiss() } }
            .onAppear { library.ensureJoined() }
            .onDisappear(perform: normalizeProfile)
        }
    }

    private func normalizeProfile() {
        focusedField = nil
        library.profileName = library.profileName.trimmingCharacters(in: .whitespacesAndNewlines)
        library.profileBio = library.profileBio.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
