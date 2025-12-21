import SwiftUI

struct GoalsListView: View {
    @StateObject private var viewModel = GoalsViewModel()
    @State private var showNewGoal = false
    @State private var selectedFilter: GoalStatus?

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.goals.isEmpty {
                    ProgressView("Loading goals...")
                } else if let error = viewModel.error {
                    VStack(spacing: 16) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.largeTitle)
                            .foregroundColor(.orange)
                        Text("Error loading goals")
                            .font(.headline)
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                        Button("Retry") {
                            Task { await viewModel.loadGoals() }
                        }
                    }
                    .padding()
                } else if viewModel.goals.isEmpty {
                    emptyState
                } else {
                    goalsList
                }
            }
            .navigationTitle("Goals")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showNewGoal = true
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
                await viewModel.loadGoals(status: selectedFilter)
            }
            .task {
                await viewModel.loadGoals()
            }
            .sheet(isPresented: $showNewGoal) {
                GoalEditorView(mode: .create) { _ in
                    Task {
                        await viewModel.loadGoals(status: selectedFilter)
                    }
                }
            }
        }
    }

    private var filterMenu: some View {
        Menu {
            Button("All") {
                selectedFilter = nil
                Task { await viewModel.loadGoals(status: nil) }
            }

            ForEach(GoalStatus.allCases, id: \.self) { status in
                Button {
                    selectedFilter = status
                    Task { await viewModel.loadGoals(status: status) }
                } label: {
                    Label(status.displayName, systemImage: status.icon)
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
            Image(systemName: "target")
                .font(.system(size: 60))
                .foregroundColor(.secondary)

            Text("No goals yet")
                .font(.title3)
                .fontWeight(.medium)

            Text("Set goals to track your progress")
                .foregroundColor(.secondary)

            Button {
                showNewGoal = true
            } label: {
                Text("Create First Goal")
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

    private var goalsList: some View {
        List {
            ForEach(viewModel.goals) { goal in
                NavigationLink {
                    GoalDetailView(goal: goal, viewModel: viewModel)
                } label: {
                    GoalRow(goal: goal)
                }
            }
            .onDelete { indexSet in
                Task {
                    for index in indexSet {
                        let goal = viewModel.goals[index]
                        await viewModel.deleteGoal(goal.id)
                    }
                }
            }
        }
        .listStyle(.plain)
    }
}

struct GoalRow: View {
    let goal: Goal

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: goal.status.icon)
                    .foregroundColor(goal.status.color)

                Text(goal.title)
                    .font(.headline)
                    .lineLimit(1)

                Spacer()

                Text("\(goal.progress)%")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .foregroundColor(.secondary)
            }

            if let description = goal.description, !description.isEmpty {
                Text(description)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            ProgressView(value: Double(goal.progress), total: 100)
                .tint(goal.status.color)

            HStack {
                Text(goal.status.displayName)
                    .font(.caption)
                    .foregroundColor(goal.status.color)

                Spacer()

                if let targetDate = goal.targetDate {
                    Text("Due: \(targetDate.formattedDate)")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    GoalsListView()
}
