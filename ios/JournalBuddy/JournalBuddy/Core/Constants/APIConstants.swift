import Foundation

enum APIConstants {
    #if DEBUG
    // Use your Mac's local IP for testing on physical device
    // Update this IP if your network changes
    static let baseURL = URL(string: "http://192.168.1.172:8000/api/v1")!
    static let wsBaseURL = URL(string: "ws://192.168.1.172:8000/api/v1")!
    #else
    static let baseURL = URL(string: "https://api.journalbuddy.app/api/v1")!
    static let wsBaseURL = URL(string: "wss://api.journalbuddy.app/api/v1")!
    #endif

    enum Endpoints {
        // Auth
        static let login = "/auth/login"
        static let signup = "/auth/signup"
        static let me = "/auth/me"
        static let refresh = "/auth/refresh"

        // Entries
        static let entries = "/entries"
        static func entry(_ id: UUID) -> String { "/entries/\(id)" }
        static func similarEntries(_ id: UUID) -> String { "/entries/\(id)/similar" }

        // Goals
        static let goals = "/goals"
        static func goal(_ id: UUID) -> String { "/goals/\(id)" }

        // Chat
        static let chatSessions = "/chat/sessions"
        static func chatSession(_ id: UUID) -> String { "/chat/sessions/\(id)" }
        static func chatMessages(_ id: UUID) -> String { "/chat/sessions/\(id)/messages" }

        // Gamification
        static let gamificationStats = "/gamification/stats"
        static let achievements = "/gamification/achievements"
        static let scheduleStatus = "/gamification/schedule-status"

        // Metrics
        static let metrics = "/metrics"

        // Summaries
        static let summaries = "/summaries"
        static let weeklySummary = "/summaries/weekly"
        static let monthlySummary = "/summaries/monthly"

        // Voice
        static let voiceChat = "/voice/chat"
        static let voices = "/voice/voices"
        static func voicePreview(_ voiceId: String) -> String { "/voice/preview/\(voiceId)" }
    }
}
