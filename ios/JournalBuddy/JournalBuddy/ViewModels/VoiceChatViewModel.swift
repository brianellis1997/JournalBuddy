import Foundation
import SwiftUI

@MainActor
class VoiceChatViewModel: ObservableObject {
    @Published var state: VoiceChatState = .disconnected
    @Published var emotion: AvatarEmotion = .neutral
    @Published var isAudioPlaying: Bool = false
    @Published var isMuted: Bool = false
    @Published var userTranscript: String = ""
    @Published var assistantText: String = ""
    @Published var conversationHistory: [(role: String, text: String)] = []
    @Published var showEndConfirmation = false
    @Published var createdEntryId: UUID?
    @Published var error: String?
    @Published var isTextOnlyMode: Bool = false
    @Published var textOnlyMessage: String?

    private let voiceChatService = VoiceChatService()

    var isListening: Bool {
        state == .listening && !isMuted
    }

    init() {
        voiceChatService.delegate = self
    }

    func startSession(journalType: String? = nil) async {
        guard let token = await KeychainManager.shared.getAccessToken() else {
            error = "Not authenticated"
            return
        }

        state = .connecting
        let voiceId = SettingsManager.shared.selectedVoiceId
        voiceChatService.start(token: token, journalType: journalType, voiceId: voiceId)
    }

    func endSession() {
        voiceChatService.stop()
        state = .disconnected
    }

    func toggleMute() {
        voiceChatService.toggleMute()
    }

    func interrupt() {
        voiceChatService.interrupt()
    }

    func clearTranscripts() {
        userTranscript = ""
        assistantText = ""
    }

    func clearError() {
        error = nil
    }
}

extension VoiceChatViewModel: VoiceChatServiceDelegate {
    nonisolated func voiceChatDidChangeState(_ state: VoiceChatState) {
        Task { @MainActor in
            self.state = state
        }
    }

    nonisolated func voiceChatDidReceiveTranscript(_ text: String, isFinal: Bool, isUser: Bool) {
        Task { @MainActor in
            if isUser {
                self.userTranscript = text
                if isFinal {
                    self.conversationHistory.append((role: "user", text: text))
                }
            }
        }
    }

    nonisolated func voiceChatDidReceiveAssistantText(_ text: String) {
        Task { @MainActor in
            guard !text.isEmpty else { return }
            self.assistantText += text
            if let lastIndex = self.conversationHistory.lastIndex(where: { $0.role == "assistant" }),
               lastIndex == self.conversationHistory.count - 1 {
                self.conversationHistory[lastIndex] = (role: "assistant", text: self.assistantText)
            } else {
                self.conversationHistory.append((role: "assistant", text: self.assistantText))
            }
        }
    }

    nonisolated func voiceChatDidReceiveEmotion(_ emotion: AvatarEmotion) {
        Task { @MainActor in
            withAnimation(.easeInOut(duration: 0.3)) {
                self.emotion = emotion
            }
        }
    }

    nonisolated func voiceChatDidEnd(entryId: UUID?) {
        Task { @MainActor in
            self.createdEntryId = entryId
            self.state = .disconnected
        }
    }

    nonisolated func voiceChatDidError(_ message: String) {
        Task { @MainActor in
            self.error = message
        }
    }

    nonisolated func voiceChatDidUpdateAudioPlaying(_ isPlaying: Bool) {
        Task { @MainActor in
            self.isAudioPlaying = isPlaying
        }
    }

    nonisolated func voiceChatDidUpdateMuted(_ isMuted: Bool) {
        Task { @MainActor in
            self.isMuted = isMuted
        }
    }

    nonisolated func voiceChatWillStartAssistantResponse() {
        Task { @MainActor in
            self.assistantText = ""
        }
    }

    nonisolated func voiceChatTTSUnavailable(_ message: String) {
        Task { @MainActor in
            self.isTextOnlyMode = true
            self.textOnlyMessage = message
        }
    }
}
