import Foundation
import SwiftUI

@MainActor
class HomeViewModel: ObservableObject {
    @Published var metrics: Metrics?
    @Published var scheduleStatus: ScheduleStatus?
    @Published var recentEntries: [Entry] = []
    @Published var isLoading = false
    @Published var error: String?

    func loadData() async {
        isLoading = true
        error = nil

        await withTaskGroup(of: Void.self) { group in
            group.addTask { await self.loadMetrics() }
            group.addTask { await self.loadScheduleStatus() }
            group.addTask { await self.loadRecentEntries() }
        }

        isLoading = false
    }

    func refresh() async {
        await loadData()
    }

    private func loadMetrics() async {
        do {
            metrics = try await APIClient.shared.getMetrics()
        } catch {
            print("Failed to load metrics: \(error)")
        }
    }

    private func loadScheduleStatus() async {
        do {
            scheduleStatus = try await APIClient.shared.getScheduleStatus()
        } catch {
            print("Failed to load schedule status: \(error)")
        }
    }

    private func loadRecentEntries() async {
        do {
            let response = try await APIClient.shared.getEntries(page: 1, limit: 5)
            recentEntries = response.entries
        } catch {
            print("Failed to load recent entries: \(error)")
        }
    }
}
