import Foundation

struct InsightsSummary: Codable {
    let moodTrends: MoodTrends
    let dayPatterns: DayPatterns
    let commonThemes: CommonThemes
    let streak: StreakInfo
    let journalTypes: JournalTypeBreakdown

    enum CodingKeys: String, CodingKey {
        case moodTrends = "mood_trends"
        case dayPatterns = "day_patterns"
        case commonThemes = "common_themes"
        case streak
        case journalTypes = "journal_types"
    }
}

struct MoodTrends: Codable {
    let periodDays: Int
    let totalEntries: Int
    let moodDistribution: [String: Int]
    let timeline: [MoodTimelineEntry]
    let averageMoodScore: Double?

    enum CodingKeys: String, CodingKey {
        case periodDays = "period_days"
        case totalEntries = "total_entries"
        case moodDistribution = "mood_distribution"
        case timeline
        case averageMoodScore = "average_mood_score"
    }
}

struct MoodTimelineEntry: Codable, Identifiable {
    var id: String { date }
    let date: String
    let avgScore: Double
    let moods: [String: Int]

    enum CodingKeys: String, CodingKey {
        case date
        case avgScore = "avg_score"
        case moods
    }
}

struct DayPatterns: Codable {
    let periodDays: Int
    let patterns: [DayPattern]
    let insights: [String]
    let bestDay: String?
    let worstDay: String?

    enum CodingKeys: String, CodingKey {
        case periodDays = "period_days"
        case patterns
        case insights
        case bestDay = "best_day"
        case worstDay = "worst_day"
    }
}

struct DayPattern: Codable, Identifiable {
    var id: Int { dayNumber }
    let day: String
    let dayNumber: Int
    let entries: Int
    let avgMoodScore: Double?
    let moods: [String: Int]

    enum CodingKeys: String, CodingKey {
        case day
        case dayNumber = "day_number"
        case entries
        case avgMoodScore = "avg_mood_score"
        case moods
    }
}

struct CommonThemes: Codable {
    let periodDays: Int
    let themes: [ThemeWord]
    let totalWordsAnalyzed: Int?
    let totalEntriesAnalyzed: Int?
    let source: String?

    enum CodingKeys: String, CodingKey {
        case periodDays = "period_days"
        case themes
        case totalWordsAnalyzed = "total_words_analyzed"
        case totalEntriesAnalyzed = "total_entries_analyzed"
        case source
    }
}

struct ThemeWord: Codable, Identifiable {
    var id: String { word }
    let word: String
    let count: Int
}

struct StreakInfo: Codable {
    let currentStreak: Int
    let longestStreak: Int
    let totalDays: Int
    let firstEntryDate: String?

    enum CodingKeys: String, CodingKey {
        case currentStreak = "current_streak"
        case longestStreak = "longest_streak"
        case totalDays = "total_days"
        case firstEntryDate = "first_entry_date"
    }
}

struct JournalTypeBreakdown: Codable {
    let periodDays: Int
    let breakdown: [JournalTypeStats]

    enum CodingKeys: String, CodingKey {
        case periodDays = "period_days"
        case breakdown
    }
}

struct JournalTypeStats: Codable, Identifiable {
    var id: String { type }
    let type: String
    let count: Int
    let avgMoodScore: Double?

    enum CodingKeys: String, CodingKey {
        case type
        case count
        case avgMoodScore = "avg_mood_score"
    }
}
