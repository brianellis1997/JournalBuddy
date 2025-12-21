import Foundation

struct ChatMessage: Codable, Identifiable {
    let id: UUID
    let role: MessageRole
    let content: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, role, content
        case createdAt = "created_at"
    }
}

enum MessageRole: String, Codable {
    case user
    case assistant
}

struct ChatSession: Codable, Identifiable {
    let id: UUID
    var entryId: UUID?
    var sessionType: String?
    var summary: String?
    var keyTopics: String?
    var goalUpdates: String?
    let createdAt: Date
    var messages: [ChatMessage]

    enum CodingKeys: String, CodingKey {
        case id
        case entryId = "entry_id"
        case sessionType = "session_type"
        case summary
        case keyTopics = "key_topics"
        case goalUpdates = "goal_updates"
        case createdAt = "created_at"
        case messages
    }
}

struct VoiceSession: Codable, Identifiable {
    let id: UUID
    let sessionType: String
    var summary: String?
    var keyTopics: String?
    var goalUpdates: String?
    let createdAt: Date
    let messageCount: Int

    enum CodingKeys: String, CodingKey {
        case id
        case sessionType = "session_type"
        case summary
        case keyTopics = "key_topics"
        case goalUpdates = "goal_updates"
        case createdAt = "created_at"
        case messageCount = "message_count"
    }
}
