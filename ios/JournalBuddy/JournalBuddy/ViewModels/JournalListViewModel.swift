import Foundation

@MainActor
class JournalListViewModel: ObservableObject {
    @Published var entries: [Entry] = []
    @Published var isLoading = false
    @Published var error: String?

    private var currentPage = 1
    private var totalEntries = 0
    private let pageSize = 20
    private var currentJournalType: JournalType?

    var hasMore: Bool {
        entries.count < totalEntries
    }

    func loadEntries(journalType: JournalType? = nil) async {
        isLoading = true
        error = nil
        currentPage = 1
        currentJournalType = journalType

        do {
            let response = try await APIClient.shared.getEntries(
                page: 1,
                limit: pageSize,
                journalType: journalType
            )
            entries = response.entries
            totalEntries = response.total
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func loadMore() async {
        guard hasMore && !isLoading else { return }

        isLoading = true
        currentPage += 1

        do {
            let response = try await APIClient.shared.getEntries(
                page: currentPage,
                limit: pageSize,
                journalType: currentJournalType
            )
            entries.append(contentsOf: response.entries)
        } catch {
            currentPage -= 1
        }

        isLoading = false
    }

    func refresh() async {
        await loadEntries(journalType: currentJournalType)
    }

    func deleteEntry(_ id: UUID) async {
        do {
            try await APIClient.shared.deleteEntry(id)
            entries.removeAll { $0.id == id }
            totalEntries -= 1
        } catch {
            self.error = error.localizedDescription
        }
    }
}
