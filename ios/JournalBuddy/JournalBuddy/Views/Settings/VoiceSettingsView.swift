import SwiftUI

struct VoiceSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @State private var voices: [Voice] = []
    @State private var isLoading = true
    @State private var error: String?

    var body: some View {
        List {
            Section {
                if isLoading {
                    HStack {
                        Spacer()
                        ProgressView()
                        Spacer()
                    }
                    .padding()
                } else if let error = error {
                    Text(error)
                        .foregroundColor(.red)
                } else {
                    ForEach(voices) { voice in
                        VoiceRow(
                            voice: voice,
                            isSelected: settingsManager.selectedVoice?.id == voice.id
                        ) {
                            settingsManager.selectedVoice = voice
                        }
                    }
                }
            } header: {
                Text("Buddy's Voice")
            } footer: {
                Text("Select the voice you'd like Buddy to use when speaking to you.")
            }
        }
        .navigationTitle("Voice Settings")
        .task {
            await loadVoices()
        }
    }

    private func loadVoices() async {
        isLoading = true
        error = nil
        do {
            voices = try await APIClient.shared.getVoices()
            if settingsManager.selectedVoice == nil, let first = voices.first {
                settingsManager.selectedVoice = first
            }
        } catch {
            self.error = "Failed to load voices"
        }
        isLoading = false
    }
}

struct VoiceRow: View {
    let voice: Voice
    let isSelected: Bool
    let onSelect: () -> Void

    var body: some View {
        Button {
            onSelect()
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(voice.name)
                        .font(.body)
                        .foregroundColor(.primary)

                    if let language = languageForVoice(voice.name) {
                        Text(language)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                Spacer()

                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.journalPrimary)
                        .font(.title3)
                }
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private func languageForVoice(_ name: String) -> String? {
        switch name.lowercased() {
        case "daniela": return "Spanish"
        case "ayush": return "Hindi"
        default: return nil
        }
    }
}

#Preview {
    NavigationStack {
        VoiceSettingsView()
    }
}
