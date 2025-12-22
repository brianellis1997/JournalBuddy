import Foundation
import SwiftUI

@MainActor
class ChatHistoryViewModel: ObservableObject {
    @Published var sessions: [VoiceSession] = []
    @Published var selectedSession: ChatSession?
    @Published var isLoading = false
    @Published var isLoadingDetail = false
    @Published var error: String?

    func loadSessions() async {
        isLoading = true
        error = nil

        do {
            sessions = try await APIClient.shared.getVoiceSessions(limit: 50)
        } catch {
            self.error = error.localizedDescription
            print("Failed to load voice sessions: \(error)")
        }

        isLoading = false
    }

    func loadSessionDetail(_ id: UUID) async {
        isLoadingDetail = true

        do {
            selectedSession = try await APIClient.shared.getChatSession(id)
        } catch {
            self.error = error.localizedDescription
            print("Failed to load session detail: \(error)")
        }

        isLoadingDetail = false
    }

    func deleteSession(_ id: UUID) async -> Bool {
        do {
            try await APIClient.shared.deleteChatSession(id)
            sessions.removeAll { $0.id == id }
            return true
        } catch {
            self.error = error.localizedDescription
            print("Failed to delete session: \(error)")
            return false
        }
    }

    func refresh() async {
        await loadSessions()
    }
}
