import SwiftUI

struct JournalListView: View {
    @StateObject private var viewModel = JournalListViewModel()
    @State private var searchText = ""
    @State private var selectedFilter: JournalType?
    @State private var showNewEntry = false

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.entries.isEmpty && !viewModel.isLoading {
                    emptyState
                } else {
                    entryList
                }
            }
            .navigationTitle("Journal")
            .searchable(text: $searchText, prompt: "Search entries...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showNewEntry = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .foregroundColor(.journalPrimary)
                    }
                }

                ToolbarItem(placement: .navigationBarLeading) {
                    filterMenu
                }
            }
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.loadEntries()
            }
            .sheet(isPresented: $showNewEntry) {
                EntryEditorView(mode: .create) { _ in
                    Task {
                        await viewModel.refresh()
                    }
                }
            }
        }
    }

    private var filterMenu: some View {
        Menu {
            Button("All") {
                selectedFilter = nil
                Task { await viewModel.loadEntries(journalType: nil) }
            }

            ForEach(JournalType.allCases, id: \.self) { type in
                Button {
                    selectedFilter = type
                    Task { await viewModel.loadEntries(journalType: type) }
                } label: {
                    Label(type.displayName, systemImage: type.icon)
                }
            }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "line.3.horizontal.decrease.circle")
                if let filter = selectedFilter {
                    Text(filter.displayName)
                        .font(.caption)
                }
            }
            .foregroundColor(.journalPrimary)
        }
    }

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "book.closed")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("No entries yet")
                .font(.title3)
                .fontWeight(.medium)

            Text("Start journaling to see your entries here")
                .foregroundColor(.secondary)

            Button {
                showNewEntry = true
            } label: {
                Text("Create First Entry")
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                    .background(
                        LinearGradient(
                            colors: [.journalPrimary, .journalSecondary],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .cornerRadius(12)
            }
        }
        .padding()
    }

    private var entryList: some View {
        List {
            ForEach(filteredEntries) { entry in
                NavigationLink {
                    EntryDetailView(entry: entry)
                } label: {
                    EntryRow(entry: entry)
                }
            }
            .onDelete { indexSet in
                Task {
                    for index in indexSet {
                        let entry = filteredEntries[index]
                        await viewModel.deleteEntry(entry.id)
                    }
                }
            }

            if viewModel.hasMore {
                ProgressView()
                    .frame(maxWidth: .infinity)
                    .onAppear {
                        Task {
                            await viewModel.loadMore()
                        }
                    }
            }
        }
        .listStyle(.plain)
    }

    private var filteredEntries: [Entry] {
        if searchText.isEmpty {
            return viewModel.entries
        }
        return viewModel.entries.filter { entry in
            entry.title?.localizedCaseInsensitiveContains(searchText) == true ||
            entry.content.localizedCaseInsensitiveContains(searchText)
        }
    }
}

struct EntryRow: View {
    let entry: Entry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                if let mood = entry.mood {
                    Text(mood.emoji)
                        .font(.title3)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text(entry.title ?? "Untitled")
                        .font(.headline)
                        .lineLimit(1)

                    Text(entry.createdAt.formattedDate)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()

                if let type = entry.journalType {
                    Image(systemName: type.icon)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Text(entry.content)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    JournalListView()
}
