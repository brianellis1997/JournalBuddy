import Foundation
import SwiftUI

@MainActor
class InsightsViewModel: ObservableObject {
    @Published var summary: InsightsSummary?
    @Published var isLoading = false
    @Published var error: String?

    var hasData: Bool {
        guard let summary = summary else { return false }
        return summary.streak.totalDays > 0
    }

    var moodEmoji: String {
        guard let avgScore = summary?.moodTrends.averageMoodScore else { return "😐" }
        switch avgScore {
        case 4.5...: return "😊"
        case 3.5..<4.5: return "🙂"
        case 2.5..<3.5: return "😐"
        case 1.5..<2.5: return "😕"
        default: return "😢"
        }
    }

    var moodDescription: String {
        guard let avgScore = summary?.moodTrends.averageMoodScore else { return "No data" }
        switch avgScore {
        case 4.5...: return "Excellent"
        case 3.5..<4.5: return "Good"
        case 2.5..<3.5: return "Okay"
        case 1.5..<2.5: return "Could be better"
        default: return "Rough patch"
        }
    }

    var sortedMoodDistribution: [(mood: String, count: Int, percentage: Double)] {
        guard let distribution = summary?.moodTrends.moodDistribution else { return [] }
        let total = Double(distribution.values.reduce(0, +))
        guard total > 0 else { return [] }

        let moodOrder = ["great", "good", "okay", "bad", "terrible"]
        return moodOrder.compactMap { mood in
            guard let count = distribution[mood] else { return nil }
            return (mood: mood, count: count, percentage: Double(count) / total)
        }
    }

    var topThemes: [ThemeWord] {
        Array(summary?.commonThemes.themes.prefix(10) ?? [])
    }

    func loadInsights() async {
        isLoading = true
        error = nil

        do {
            summary = try await APIClient.shared.getInsightsSummary()
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func moodColor(for mood: String) -> Color {
        switch mood.lowercased() {
        case "great": return .green
        case "good": return .mint
        case "okay": return .yellow
        case "bad": return .orange
        case "terrible": return .red
        default: return .gray
        }
    }

    func moodEmoji(for mood: String) -> String {
        switch mood.lowercased() {
        case "great": return "😊"
        case "good": return "🙂"
        case "okay": return "😐"
        case "bad": return "😕"
        case "terrible": return "😢"
        default: return "❓"
        }
    }
}
