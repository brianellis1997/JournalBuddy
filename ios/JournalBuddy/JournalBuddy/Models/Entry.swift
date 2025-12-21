import Foundation

enum MoodType: String, Codable, CaseIterable {
    case great
    case good
    case okay
    case bad
    case terrible

    var emoji: String {
        switch self {
        case .great: return "😄"
        case .good: return "🙂"
        case .okay: return "😐"
        case .bad: return "😔"
        case .terrible: return "😢"
        }
    }

    var displayName: String {
        rawValue.capitalized
    }
}

enum JournalType: String, Codable, CaseIterable {
    case morning
    case evening
    case freeform

    var displayName: String {
        rawValue.capitalized
    }

    var icon: String {
        switch self {
        case .morning: return "sunrise.fill"
        case .evening: return "moon.stars.fill"
        case .freeform: return "pencil"
        }
    }
}

struct Entry: Codable, Identifiable {
    let id: UUID
    var title: String?
    var content: String
    var transcript: String?
    var mood: MoodType?
    var journalType: JournalType?
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, content, transcript, mood
        case journalType = "journal_type"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct EntryCreate: Codable {
    var title: String?
    var content: String
    var transcript: String?
    var mood: MoodType?
    var journalType: JournalType?

    enum CodingKeys: String, CodingKey {
        case title, content, transcript, mood
        case journalType = "journal_type"
    }
}

struct EntryUpdate: Codable {
    var title: String?
    var content: String?
    var mood: MoodType?
    var journalType: JournalType?

    enum CodingKeys: String, CodingKey {
        case title, content, mood
        case journalType = "journal_type"
    }
}

struct EntryListResponse: Codable {
    let entries: [Entry]
    let total: Int
    let page: Int
    let limit: Int
}
