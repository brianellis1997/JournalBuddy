import Foundation
import SwiftUI

@MainActor
class GamificationViewModel: ObservableObject {
    @Published var stats: GamificationStats?
    @Published var isLoading = false
    @Published var error: String?

    var levelProgress: Double {
        guard let stats = stats, stats.xpForNextLevel > 0 else { return 0 }
        return Double(stats.xpProgressInLevel) / Double(stats.xpForNextLevel)
    }

    var unlockedAchievements: [Achievement] {
        stats?.achievements.filter { $0.isUnlocked } ?? []
    }

    var lockedAchievements: [Achievement] {
        stats?.achievements.filter { !$0.isUnlocked } ?? []
    }

    func loadStats() async {
        isLoading = true
        error = nil

        do {
            stats = try await APIClient.shared.getGamificationStats()
        } catch {
            self.error = error.localizedDescription
            print("Failed to load gamification stats: \(error)")
        }

        isLoading = false
    }

    func refresh() async {
        await loadStats()
    }
}
