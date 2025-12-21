import SwiftUI

struct VoiceChatView: View {
    @StateObject private var viewModel = VoiceChatViewModel()
    @Environment(\.dismiss) private var dismiss

    let journalType: String?

    init(journalType: String? = nil) {
        self.journalType = journalType
    }

    var body: some View {
        ZStack {
            backgroundGradient

            VStack(spacing: 0) {
                header

                Spacer()

                avatarSection

                Spacer()

                transcriptSection

                controlsSection
            }
        }
        .task {
            await viewModel.startSession(journalType: journalType)
        }
        .onDisappear {
            viewModel.endSession()
        }
        .alert("Error", isPresented: .init(
            get: { viewModel.error != nil },
            set: { if !$0 { viewModel.clearError() } }
        )) {
            Button("OK") { viewModel.clearError() }
        } message: {
            Text(viewModel.error ?? "")
        }
        .alert("End Session?", isPresented: $viewModel.showEndConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("End", role: .destructive) {
                viewModel.endSession()
                dismiss()
            }
        } message: {
            Text("Are you sure you want to end this voice session?")
        }
        .onChange(of: viewModel.createdEntryId) { _, entryId in
            if entryId != nil {
                dismiss()
            }
        }
    }

    private var backgroundGradient: some View {
        LinearGradient(
            colors: [
                Color(red: 0.05, green: 0.05, blue: 0.15),
                Color(red: 0.1, green: 0.05, blue: 0.2)
            ],
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()
    }

    private var header: some View {
        HStack {
            Button {
                if viewModel.state != .disconnected {
                    viewModel.showEndConfirmation = true
                } else {
                    dismiss()
                }
            } label: {
                Image(systemName: "xmark.circle.fill")
                    .font(.title2)
                    .foregroundColor(.white.opacity(0.7))
            }

            Spacer()

            VStack(spacing: 2) {
                Text("Voice Journal")
                    .font(.headline)
                    .foregroundColor(.white)

                Text(viewModel.state.statusText)
                    .font(.caption)
                    .foregroundColor(statusColor)
            }

            Spacer()

            Circle()
                .fill(statusColor)
                .frame(width: 12, height: 12)
        }
        .padding()
    }

    private var statusColor: Color {
        switch viewModel.state {
        case .disconnected: return .red
        case .connecting: return .orange
        case .idle: return .green
        case .listening: return .green
        case .thinking: return .purple
        case .speaking: return .blue
        }
    }

    private var avatarSection: some View {
        VStack(spacing: 20) {
            AvatarView(state: viewModel.state, emotion: viewModel.emotion, isAudioPlaying: viewModel.isAudioPlaying)

            if viewModel.isListening {
                AudioWaveformView(isActive: true, color: .green)
                    .frame(height: 30)
            } else if viewModel.state == .speaking && viewModel.isAudioPlaying {
                AudioWaveformView(isActive: true, color: .journalSecondary)
                    .frame(height: 30)
            } else if viewModel.isMuted {
                HStack(spacing: 8) {
                    Image(systemName: "mic.slash.fill")
                        .foregroundColor(.red.opacity(0.7))
                    Text("Muted")
                        .font(.caption)
                        .foregroundColor(.white.opacity(0.6))
                }
                .frame(height: 30)
            } else {
                Spacer()
                    .frame(height: 30)
            }
        }
    }

    private var transcriptSection: some View {
        VStack(spacing: 12) {
            if !viewModel.userTranscript.isEmpty {
                HStack {
                    Spacer()
                    Text(viewModel.userTranscript)
                        .font(.body)
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.green.opacity(0.3))
                        .cornerRadius(16)
                        .frame(maxWidth: 280, alignment: .trailing)
                }
            }

            if !viewModel.assistantText.isEmpty {
                HStack {
                    Text(viewModel.assistantText)
                        .font(.body)
                        .foregroundColor(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.journalPrimary.opacity(0.3))
                        .cornerRadius(16)
                        .frame(maxWidth: 280, alignment: .leading)
                    Spacer()
                }
            }
        }
        .padding(.horizontal)
        .frame(minHeight: 120)
    }

    private var controlsSection: some View {
        VStack(spacing: 16) {
            if viewModel.state == .speaking && viewModel.isAudioPlaying {
                Button {
                    viewModel.interrupt()
                } label: {
                    HStack {
                        Image(systemName: "hand.raised.fill")
                        Text("Interrupt")
                    }
                    .font(.subheadline)
                    .foregroundColor(.white.opacity(0.8))
                    .padding(.horizontal, 20)
                    .padding(.vertical, 10)
                    .background(Color.white.opacity(0.2))
                    .cornerRadius(20)
                }
            }

            muteButton
                .padding(.bottom, 40)
        }
    }

    private var muteButton: some View {
        Button {
            viewModel.toggleMute()
        } label: {
            ZStack {
                Circle()
                    .fill(muteButtonColor)
                    .frame(width: 80, height: 80)
                    .shadow(color: muteButtonColor.opacity(0.5), radius: 10)

                if viewModel.state == .connecting {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                        .scaleEffect(1.5)
                } else {
                    Image(systemName: muteButtonIcon)
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.white)
                }
            }
        }
        .disabled(viewModel.state == .connecting || viewModel.state == .disconnected)
        .scaleEffect(viewModel.isListening ? 1.1 : 1.0)
        .animation(.easeInOut(duration: 0.2), value: viewModel.isListening)
    }

    private var muteButtonColor: Color {
        if viewModel.state == .connecting || viewModel.state == .disconnected {
            return .gray
        }
        return viewModel.isMuted ? .red : .green
    }

    private var muteButtonIcon: String {
        if viewModel.state == .connecting {
            return "mic.fill"
        }
        return viewModel.isMuted ? "mic.slash.fill" : "mic.fill"
    }
}

#Preview {
    VoiceChatView()
}
