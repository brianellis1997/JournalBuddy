import Foundation

@MainActor
class GoalsViewModel: ObservableObject {
    @Published var goals: [Goal] = []
    @Published var isLoading = false
    @Published var error: String?

    func loadGoals(status: GoalStatus? = nil) async {
        isLoading = true
        error = nil

        do {
            goals = try await APIClient.shared.getGoals(status: status)
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func updateGoal(_ id: UUID, _ update: GoalUpdate) async {
        do {
            let updated = try await APIClient.shared.updateGoal(id, update)
            if let index = goals.firstIndex(where: { $0.id == id }) {
                goals[index] = updated
            }
        } catch {
            self.error = error.localizedDescription
        }
    }

    func deleteGoal(_ id: UUID) async {
        do {
            try await APIClient.shared.deleteGoal(id)
            goals.removeAll { $0.id == id }
        } catch {
            self.error = error.localizedDescription
        }
    }
}
