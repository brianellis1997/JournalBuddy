import SwiftUI
import AVFoundation

@MainActor
class VoicePreviewPlayer: ObservableObject {
    private var audioEngine: AVAudioEngine?
    private var playerNode: AVAudioPlayerNode?
    @Published var isPlaying = false
    @Published var loadingVoiceId: String?

    func playPreview(voiceId: String) async {
        loadingVoiceId = voiceId
        stop()

        do {
            let audioData = try await APIClient.shared.getVoicePreview(voiceId: voiceId)
            loadingVoiceId = nil
            playPCMAudio(audioData)
        } catch {
            loadingVoiceId = nil
            print("[VoicePreview] Error: \(error)")
        }
    }

    private func playPCMAudio(_ data: Data) {
        stop()

        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
        } catch {
            print("[VoicePreview] Failed to configure audio session: \(error)")
            return
        }

        audioEngine = AVAudioEngine()
        playerNode = AVAudioPlayerNode()

        guard let engine = audioEngine, let node = playerNode else { return }

        engine.attach(node)

        let sampleRate: Double = 24000
        guard let format = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: sampleRate, channels: 1, interleaved: true) else {
            return
        }

        engine.connect(node, to: engine.mainMixerNode, format: format)
        engine.mainMixerNode.outputVolume = 4.0

        let frameCount = UInt32(data.count / 2)
        guard let int16Format = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: sampleRate, channels: 1, interleaved: true),
              let int16Buffer = AVAudioPCMBuffer(pcmFormat: int16Format, frameCapacity: frameCount),
              let floatBuffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount),
              let converter = AVAudioConverter(from: int16Format, to: format) else {
            return
        }

        int16Buffer.frameLength = frameCount
        data.withUnsafeBytes { rawBuffer in
            if let baseAddress = rawBuffer.baseAddress {
                memcpy(int16Buffer.int16ChannelData![0], baseAddress, data.count)
            }
        }

        floatBuffer.frameLength = frameCount
        var error: NSError?
        converter.convert(to: floatBuffer, error: &error) { _, outStatus in
            outStatus.pointee = .haveData
            return int16Buffer
        }

        do {
            try engine.start()
            node.play()
            isPlaying = true

            node.scheduleBuffer(floatBuffer) { [weak self] in
                Task { @MainActor in
                    self?.isPlaying = false
                }
            }
        } catch {
            print("[VoicePreview] Failed to start engine: \(error)")
        }
    }

    func stop() {
        playerNode?.stop()
        audioEngine?.stop()
        audioEngine = nil
        playerNode = nil
        isPlaying = false
    }
}

struct VoiceSettingsView: View {
    @StateObject private var settingsManager = SettingsManager.shared
    @StateObject private var previewPlayer = VoicePreviewPlayer()
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
                            isSelected: settingsManager.selectedVoice?.id == voice.id,
                            isLoading: previewPlayer.loadingVoiceId == voice.id,
                            isPlaying: previewPlayer.isPlaying && settingsManager.selectedVoice?.id == voice.id
                        ) {
                            settingsManager.selectedVoice = voice
                            Task {
                                await previewPlayer.playPreview(voiceId: voice.id)
                            }
                        }
                    }
                }
            } header: {
                Text("Buddy's Voice")
            } footer: {
                Text("Tap a voice to select it and hear a preview.")
            }
        }
        .navigationTitle("Voice Settings")
        .task {
            await loadVoices()
        }
        .onDisappear {
            previewPlayer.stop()
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
    let isLoading: Bool
    let isPlaying: Bool
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

                if isLoading {
                    ProgressView()
                        .scaleEffect(0.8)
                } else if isPlaying {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundColor(.journalPrimary)
                        .font(.body)
                } else if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.journalPrimary)
                        .font(.title3)
                } else {
                    Image(systemName: "play.circle")
                        .foregroundColor(.secondary)
                        .font(.title3)
                }
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(isLoading)
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
