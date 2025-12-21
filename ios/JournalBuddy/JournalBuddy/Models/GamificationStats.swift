import Foundation

struct GamificationStats: Codable {
    let totalXP: Int
    let level: Int
    let xpForNextLevel: Int
    let xpProgressInLevel: Int
    let currentStreak: Int
    let longestStreak: Int
    let achievements: [Achievement]
    let recentXPEvents: [XPEvent]

    enum CodingKeys: String, CodingKey {
        case totalXP = "total_xp"
        case level
        case xpForNextLevel = "xp_for_next_level"
        case xpProgressInLevel = "xp_progress_in_level"
        case currentStreak = "current_streak"
        case longestStreak = "longest_streak"
        case achievements
        case recentXPEvents = "recent_xp_events"
    }
}

struct Achievement: Codable, Identifiable {
    var id: String { key }
    let key: String
    let name: String
    let description: String
    let icon: String
    var unlockedAt: Date?
    var progress: Int?
    var target: Int?

    enum CodingKeys: String, CodingKey {
        case key, name, description, icon
        case unlockedAt = "unlocked_at"
        case progress, target
    }

    var isUnlocked: Bool {
        unlockedAt != nil
    }

    var progressPercentage: Double {
        guard let progress = progress, let target = target, target > 0 else { return 0 }
        return Double(progress) / Double(target)
    }
}

struct XPEvent: Codable, Identifiable {
    var id: String { "\(eventType)-\(createdAt.timeIntervalSince1970)" }
    let eventType: String
    let xpAmount: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case eventType = "event_type"
        case xpAmount = "xp_amount"
        case createdAt = "created_at"
    }
}

struct Metrics: Codable {
    let totalEntries: Int
    let currentStreak: Int
    let longestStreak: Int
    let entriesThisWeek: Int
    let entriesThisMonth: Int
    let totalGoals: Int
    let activeGoals: Int
    let completedGoals: Int
    let totalXP: Int
    let level: Int
    let morningCompletedToday: Bool
    let eveningCompletedToday: Bool

    enum CodingKeys: String, CodingKey {
        case totalEntries = "total_entries"
        case currentStreak = "current_streak"
        case longestStreak = "longest_streak"
        case entriesThisWeek = "entries_this_week"
        case entriesThisMonth = "entries_this_month"
        case totalGoals = "total_goals"
        case activeGoals = "active_goals"
        case completedGoals = "completed_goals"
        case totalXP = "total_xp"
        case level
        case morningCompletedToday = "morning_completed_today"
        case eveningCompletedToday = "evening_completed_today"
    }
}

struct ScheduleStatus: Codable {
    let morningCompleted: Bool
    let eveningCompleted: Bool
    let morningPrompt: String?
    let eveningPrompt: String?
    let shouldShowMorning: Bool
    let shouldShowEvening: Bool

    enum CodingKeys: String, CodingKey {
        case morningCompleted = "morning_completed"
        case eveningCompleted = "evening_completed"
        case morningPrompt = "morning_prompt"
        case eveningPrompt = "evening_prompt"
        case shouldShowMorning = "should_show_morning"
        case shouldShowEvening = "should_show_evening"
    }
}
