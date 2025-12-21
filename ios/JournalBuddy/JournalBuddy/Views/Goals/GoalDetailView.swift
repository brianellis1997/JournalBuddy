import SwiftUI

struct GoalDetailView: View {
    let goal: Goal
    @ObservedObject var viewModel: GoalsViewModel
    @State private var showEdit = false
    @State private var progress: Double
    @Environment(\.dismiss) private var dismiss

    init(goal: Goal, viewModel: GoalsViewModel) {
        self.goal = goal
        self.viewModel = viewModel
        _progress = State(initialValue: Double(goal.progress))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                headerSection

                progressSection

                if let description = goal.description, !description.isEmpty {
                    descriptionSection(description)
                }

                detailsSection

                actionsSection
            }
            .padding()
        }
        .navigationTitle(goal.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Edit") {
                    showEdit = true
                }
            }
        }
        .sheet(isPresented: $showEdit) {
            GoalEditorView(mode: .edit(goal)) { _ in
                Task {
                    await viewModel.loadGoals()
                }
            }
        }
    }

    private var headerSection: some View {
        HStack {
            Image(systemName: goal.status.icon)
                .font(.title)
                .foregroundColor(goal.status.color)

            VStack(alignment: .leading) {
                Text(goal.status.displayName)
                    .font(.headline)
                    .foregroundColor(goal.status.color)

                Text("Created \(goal.createdAt.relativeString)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
    }

    private var progressSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Progress")
                    .font(.headline)

                Spacer()

                Text("\(Int(progress))%")
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundColor(goal.status.color)
            }

            ProgressView(value: progress, total: 100)
                .tint(goal.status.color)
                .scaleEffect(y: 2)

            Slider(value: $progress, in: 0...100, step: 5) { editing in
                if !editing {
                    Task {
                        await viewModel.updateGoal(goal.id, GoalUpdate(progress: Int(progress)))
                    }
                }
            }
            .tint(goal.status.color)
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
    }

    private func descriptionSection(_ description: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Description")
                .font(.headline)

            Text(description)
                .foregroundColor(.secondary)
        }
    }

    private var detailsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Details")
                .font(.headline)

            if let targetDate = goal.targetDate {
                HStack {
                    Image(systemName: "calendar")
                        .foregroundColor(.secondary)
                    Text("Target Date")
                    Spacer()
                    Text(targetDate.formattedDate)
                        .foregroundColor(.secondary)
                }
            }

            if let schedule = goal.journalingSchedule {
                HStack {
                    Image(systemName: "clock")
                        .foregroundColor(.secondary)
                    Text("Journal Schedule")
                    Spacer()
                    Text(schedule.displayName)
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
    }

    private var actionsSection: some View {
        VStack(spacing: 12) {
            if goal.status == .active {
                Button {
                    Task {
                        await viewModel.updateGoal(goal.id, GoalUpdate(status: .completed, progress: 100))
                        dismiss()
                    }
                } label: {
                    Label("Mark as Complete", systemImage: "checkmark.circle.fill")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.success)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }

                Button {
                    Task {
                        await viewModel.updateGoal(goal.id, GoalUpdate(status: .paused))
                    }
                } label: {
                    Label("Pause Goal", systemImage: "pause.circle")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.secondaryBackground)
                        .cornerRadius(12)
                }
            }

            if goal.status == .paused {
                Button {
                    Task {
                        await viewModel.updateGoal(goal.id, GoalUpdate(status: .active))
                    }
                } label: {
                    Label("Resume Goal", systemImage: "play.circle.fill")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.journalPrimary)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        GoalDetailView(
            goal: Goal(
                id: UUID(),
                title: "Learn Swift",
                description: "Complete the iOS development course and build 3 apps",
                status: .active,
                progress: 45,
                targetDate: Date().addingTimeInterval(86400 * 30),
                journalingSchedule: .morning,
                createdAt: Date(),
                updatedAt: Date()
            ),
            viewModel: GoalsViewModel()
        )
    }
}
