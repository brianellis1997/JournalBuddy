import SwiftUI

struct EntryDetailView: View {
    let entry: Entry
    @State private var showEdit = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                headerSection

                Divider()

                contentSection

                if let transcript = entry.transcript, !transcript.isEmpty {
                    Divider()
                    transcriptSection(transcript)
                }
            }
            .padding()
        }
        .navigationTitle(entry.title ?? "Entry")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showEdit = true
                } label: {
                    Text("Edit")
                }
            }
        }
        .sheet(isPresented: $showEdit) {
            EntryEditorView(mode: .edit(entry)) { _ in }
        }
    }

    private var headerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                if let mood = entry.mood {
                    HStack(spacing: 6) {
                        Text(mood.emoji)
                        Text(mood.displayName)
                            .font(.subheadline)
                            .foregroundColor(mood.color)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(mood.color.opacity(0.1))
                    .cornerRadius(20)
                }

                if let type = entry.journalType {
                    HStack(spacing: 6) {
                        Image(systemName: type.icon)
                        Text(type.displayName)
                            .font(.subheadline)
                    }
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 6)
                    .background(Color.secondaryBackground)
                    .cornerRadius(20)
                }

                Spacer()
            }

            Text(entry.createdAt.formattedDateTime)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }

    private var contentSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Entry")
                .font(.headline)

            Text(entry.content)
                .font(.body)
        }
    }

    private func transcriptSection(_ transcript: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "waveform")
                Text("Voice Transcript")
                    .font(.headline)
            }

            Text(transcript)
                .font(.body)
                .foregroundColor(.secondary)
                .padding()
                .background(Color.secondaryBackground)
                .cornerRadius(12)
        }
    }
}

#Preview {
    NavigationStack {
        EntryDetailView(entry: Entry(
            id: UUID(),
            title: "A Great Day",
            content: "Today was wonderful. I accomplished so much and felt really productive.",
            transcript: "You: I had a great day today.\nJournalBuddy: That's wonderful to hear!",
            mood: .great,
            journalType: .morning,
            createdAt: Date(),
            updatedAt: Date()
        ))
    }
}
