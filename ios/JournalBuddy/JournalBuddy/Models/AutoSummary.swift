import Foundation

enum PeriodType: String, Codable {
    case weekly
    case monthly
}

enum MoodTrend: String, Codable {
    case improving
    case stable
    case declining
    case mixed
}

struct AutoSummary: Codable, Identifiable {
    let id: UUID
    let periodType: PeriodType
    let periodStart: Date
    let periodEnd: Date
    let title: String
    let content: String
    var moodTrend: MoodTrend?
    var keyThemes: String?
    var goalProgress: String?
    let entryCount: Int
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case periodType = "period_type"
        case periodStart = "period_start"
        case periodEnd = "period_end"
        case title, content
        case moodTrend = "mood_trend"
        case keyThemes = "key_themes"
        case goalProgress = "goal_progress"
        case entryCount = "entry_count"
        case createdAt = "created_at"
    }
}

struct AutoSummaryListResponse: Codable {
    let summaries: [AutoSummary]
    let total: Int
}

struct GenerateSummaryResponse: Codable {
    let summary: AutoSummary
    let isNew: Bool

    enum CodingKeys: String, CodingKey {
        case summary
        case isNew = "is_new"
    }
}
