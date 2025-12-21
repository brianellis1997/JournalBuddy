import SwiftUI

enum GoalEditorMode {
    case create
    case edit(Goal)

    var title: String {
        switch self {
        case .create: return "New Goal"
        case .edit: return "Edit Goal"
        }
    }
}

struct GoalEditorView: View {
    let mode: GoalEditorMode
    let onSave: (Goal) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var description = ""
    @State private var hasTargetDate = false
    @State private var targetDate = Date()
    @State private var journalingSchedule: JournalingSchedule?
    @State private var isSaving = false
    @State private var error: String?

    init(mode: GoalEditorMode, onSave: @escaping (Goal) -> Void) {
        self.mode = mode
        self.onSave = onSave

        if case .edit(let goal) = mode {
            _title = State(initialValue: goal.title)
            _description = State(initialValue: goal.description ?? "")
            _hasTargetDate = State(initialValue: goal.targetDate != nil)
            _targetDate = State(initialValue: goal.targetDate ?? Date())
            _journalingSchedule = State(initialValue: goal.journalingSchedule)
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Goal") {
                    TextField("Goal title", text: $title)

                    TextField("Description (optional)", text: $description, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section("Target Date") {
                    Toggle("Set target date", isOn: $hasTargetDate)

                    if hasTargetDate {
                        DatePicker(
                            "Target",
                            selection: $targetDate,
                            in: Date()...,
                            displayedComponents: .date
                        )
                    }
                }

                Section("Journaling Schedule") {
                    Picker("Schedule", selection: $journalingSchedule) {
                        Text("None").tag(nil as JournalingSchedule?)
                        ForEach(JournalingSchedule.allCases, id: \.self) { schedule in
                            Text(schedule.displayName).tag(schedule as JournalingSchedule?)
                        }
                    }
                    .pickerStyle(.segmented)

                    Text("Link this goal to your journaling routine for regular check-ins")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                if let error = error {
                    Section {
                        Text(error)
                            .foregroundColor(.error)
                    }
                }
            }
            .navigationTitle(mode.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task { await save() }
                    } label: {
                        if isSaving {
                            ProgressView()
                        } else {
                            Text("Save")
                                .fontWeight(.semibold)
                        }
                    }
                    .disabled(title.isEmpty || isSaving)
                }
            }
        }
    }

    private func save() async {
        isSaving = true
        error = nil

        do {
            let goal: Goal
            switch mode {
            case .create:
                let create = GoalCreate(
                    title: title,
                    description: description.isEmpty ? nil : description,
                    targetDate: hasTargetDate ? targetDate : nil,
                    journalingSchedule: journalingSchedule
                )
                goal = try await APIClient.shared.createGoal(create)
            case .edit(let existing):
                let update = GoalUpdate(
                    title: title,
                    description: description.isEmpty ? nil : description,
                    targetDate: hasTargetDate ? targetDate : nil,
                    journalingSchedule: journalingSchedule
                )
                goal = try await APIClient.shared.updateGoal(existing.id, update)
            }
            onSave(goal)
            dismiss()
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }
}

#Preview {
    GoalEditorView(mode: .create) { _ in }
}
