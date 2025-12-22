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
        error = nil

        do {
            selectedSession = try await APIClient.shared.getChatSession(id)
            print("Successfully loaded session detail: \(id), messages: \(selectedSession?.messages.count ?? 0)")
        } catch let decodingError as DecodingError {
            self.error = "Failed to decode response: \(decodingError.localizedDescription)"
            print("Decoding error loading session detail: \(decodingError)")
            if case .dataCorrupted(let context) = decodingError {
                print("  Context: \(context)")
            } else if case .keyNotFound(let key, let context) = decodingError {
                print("  Key not found: \(key), context: \(context)")
            } else if case .typeMismatch(let type, let context) = decodingError {
                print("  Type mismatch: \(type), context: \(context)")
            } else if case .valueNotFound(let type, let context) = decodingError {
                print("  Value not found: \(type), context: \(context)")
            }
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
