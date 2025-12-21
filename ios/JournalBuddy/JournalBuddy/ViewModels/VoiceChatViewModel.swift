import Foundation
import SwiftUI

@MainActor
class VoiceChatViewModel: ObservableObject {
    @Published var state: VoiceChatState = .disconnected
    @Published var emotion: AvatarEmotion = .neutral
    @Published var userTranscript: String = ""
    @Published var assistantText: String = ""
    @Published var conversationHistory: [(role: String, text: String)] = []
    @Published var showEndConfirmation = false
    @Published var createdEntryId: UUID?
    @Published var error: String?

    private let voiceChatService = VoiceChatService()

    var isRecording: Bool {
        state == .listening
    }

    var canRecord: Bool {
        state == .idle || state == .speaking
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
        voiceChatService.start(token: token, journalType: journalType)
    }

    func endSession() {
        voiceChatService.stop()
        state = .disconnected
    }

    func toggleRecording() {
        if state == .listening {
            voiceChatService.stopRecording()
        } else if canRecord {
            userTranscript = ""
            voiceChatService.startRecording()
        }
    }

    func interrupt() {
        voiceChatService.interrupt()
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
            self.assistantText = text
            if !text.isEmpty {
                if let lastIndex = self.conversationHistory.lastIndex(where: { $0.role == "assistant" }),
                   lastIndex == self.conversationHistory.count - 1 {
                    self.conversationHistory[lastIndex] = (role: "assistant", text: text)
                } else {
                    self.conversationHistory.append((role: "assistant", text: text))
                }
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
}
