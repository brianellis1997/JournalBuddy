import SwiftUI

enum EntryEditorMode {
    case create
    case edit(Entry)

    var title: String {
        switch self {
        case .create: return "New Entry"
        case .edit: return "Edit Entry"
        }
    }
}

struct EntryEditorView: View {
    let mode: EntryEditorMode
    let onSave: (Entry) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title = ""
    @State private var content = ""
    @State private var selectedMood: MoodType?
    @State private var selectedType: JournalType?
    @State private var isSaving = false
    @State private var error: String?

    init(mode: EntryEditorMode, onSave: @escaping (Entry) -> Void) {
        self.mode = mode
        self.onSave = onSave

        if case .edit(let entry) = mode {
            _title = State(initialValue: entry.title ?? "")
            _content = State(initialValue: entry.content)
            _selectedMood = State(initialValue: entry.mood)
            _selectedType = State(initialValue: entry.journalType)
        }
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Title") {
                    TextField("Entry title (optional)", text: $title)
                }

                Section("Content") {
                    TextEditor(text: $content)
                        .frame(minHeight: 200)
                }

                Section("Mood") {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 12) {
                            ForEach(MoodType.allCases, id: \.self) { mood in
                                MoodButton(
                                    mood: mood,
                                    isSelected: selectedMood == mood
                                ) {
                                    selectedMood = mood
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                }

                Section("Type") {
                    Picker("Journal Type", selection: $selectedType) {
                        Text("None").tag(nil as JournalType?)
                        ForEach(JournalType.allCases, id: \.self) { type in
                            Label(type.displayName, systemImage: type.icon)
                                .tag(type as JournalType?)
                        }
                    }
                    .pickerStyle(.segmented)
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
                    .disabled(content.isEmpty || isSaving)
                }
            }
        }
    }

    private func save() async {
        isSaving = true
        error = nil

        do {
            let entry: Entry
            switch mode {
            case .create:
                let create = EntryCreate(
                    title: title.isEmpty ? nil : title,
                    content: content,
                    mood: selectedMood,
                    journalType: selectedType
                )
                entry = try await APIClient.shared.createEntry(create)
            case .edit(let existing):
                let update = EntryUpdate(
                    title: title.isEmpty ? nil : title,
                    content: content,
                    mood: selectedMood,
                    journalType: selectedType
                )
                entry = try await APIClient.shared.updateEntry(existing.id, update)
            }
            onSave(entry)
            dismiss()
        } catch {
            self.error = error.localizedDescription
        }

        isSaving = false
    }
}

struct MoodButton: View {
    let mood: MoodType
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(mood.emoji)
                    .font(.title2)
                Text(mood.displayName)
                    .font(.caption2)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isSelected ? mood.color.opacity(0.2) : Color.secondaryBackground)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? mood.color : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    EntryEditorView(mode: .create) { _ in }
}
