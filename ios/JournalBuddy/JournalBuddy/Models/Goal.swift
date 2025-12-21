import Foundation

enum GoalStatus: String, Codable, CaseIterable {
    case active
    case completed
    case paused
    case abandoned

    var displayName: String {
        rawValue.capitalized
    }

    var icon: String {
        switch self {
        case .active: return "target"
        case .completed: return "checkmark.circle.fill"
        case .paused: return "pause.circle"
        case .abandoned: return "xmark.circle"
        }
    }
}

enum JournalingSchedule: String, Codable, CaseIterable {
    case morning
    case evening
    case both

    var displayName: String {
        switch self {
        case .morning: return "Morning"
        case .evening: return "Evening"
        case .both: return "Both"
        }
    }
}

struct Goal: Codable, Identifiable {
    let id: UUID
    var title: String
    var description: String?
    var status: GoalStatus
    var progress: Int
    var targetDate: Date?
    var journalingSchedule: JournalingSchedule?
    let createdAt: Date
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, title, description, status, progress
        case targetDate = "target_date"
        case journalingSchedule = "journaling_schedule"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct GoalCreate: Codable {
    var title: String
    var description: String?
    var targetDate: Date?
    var journalingSchedule: JournalingSchedule?

    enum CodingKeys: String, CodingKey {
        case title, description
        case targetDate = "target_date"
        case journalingSchedule = "journaling_schedule"
    }
}

struct GoalUpdate: Codable {
    var title: String?
    var description: String?
    var status: GoalStatus?
    var progress: Int?
    var targetDate: Date?
    var journalingSchedule: JournalingSchedule?

    enum CodingKeys: String, CodingKey {
        case title, description, status, progress
        case targetDate = "target_date"
        case journalingSchedule = "journaling_schedule"
    }
}
