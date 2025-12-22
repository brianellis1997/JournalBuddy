import SwiftUI

struct ChatHistoryView: View {
    @StateObject private var viewModel = ChatHistoryViewModel()
    @State private var showDeleteConfirmation = false
    @State private var sessionToDelete: UUID?

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.sessions.isEmpty {
                loadingView
            } else if viewModel.sessions.isEmpty {
                emptyView
            } else {
                sessionsList
            }
        }
        .navigationTitle("Chat History")
        .refreshable {
            await viewModel.refresh()
        }
        .task {
            await viewModel.loadSessions()
        }
        .alert("Delete Conversation", isPresented: $showDeleteConfirmation) {
            Button("Cancel", role: .cancel) {}
            Button("Delete", role: .destructive) {
                if let id = sessionToDelete {
                    Task {
                        _ = await viewModel.deleteSession(id)
                    }
                }
            }
        } message: {
            Text("Are you sure you want to delete this conversation? This cannot be undone.")
        }
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
            Text("Loading conversations...")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var emptyView: some View {
        VStack(spacing: 16) {
            Image(systemName: "bubble.left.and.bubble.right")
                .font(.system(size: 60))
                .foregroundColor(.gray.opacity(0.5))

            Text("No Conversations Yet")
                .font(.title3)
                .fontWeight(.semibold)

            Text("Start a voice chat with Buddy\nto see your conversation history here.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var sessionsList: some View {
        List {
            ForEach(viewModel.sessions) { session in
                NavigationLink {
                    ChatSessionDetailView(sessionId: session.id)
                } label: {
                    SessionRow(session: session)
                }
                .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                    Button(role: .destructive) {
                        sessionToDelete = session.id
                        showDeleteConfirmation = true
                    } label: {
                        Label("Delete", systemImage: "trash")
                    }
                }
            }
        }
        .listStyle(.plain)
    }
}

struct SessionRow: View {
    let session: VoiceSession

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: iconForSessionType(session.sessionType))
                    .foregroundColor(colorForSessionType(session.sessionType))

                Text(displayNameForSessionType(session.sessionType))
                    .font(.subheadline)
                    .fontWeight(.medium)

                Spacer()

                Text(session.createdAt.relativeString)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            if let summary = session.summary, !summary.isEmpty {
                Text(summary)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }

            HStack(spacing: 12) {
                Label("\(session.messageCount) messages", systemImage: "bubble.left.and.bubble.right")
                    .font(.caption2)
                    .foregroundColor(.secondary)

                if let topics = session.keyTopics, !topics.isEmpty {
                    Text(topics)
                        .font(.caption2)
                        .foregroundColor(.journalPrimary)
                        .lineLimit(1)
                }
            }
        }
        .padding(.vertical, 4)
    }

    private func iconForSessionType(_ type: String) -> String {
        switch type {
        case "morning": return "sunrise.fill"
        case "evening": return "moon.stars.fill"
        default: return "waveform.circle.fill"
        }
    }

    private func colorForSessionType(_ type: String) -> Color {
        switch type {
        case "morning": return .orange
        case "evening": return .indigo
        default: return .journalPrimary
        }
    }

    private func displayNameForSessionType(_ type: String) -> String {
        switch type {
        case "morning": return "Morning Journal"
        case "evening": return "Evening Reflection"
        default: return "Freeform Chat"
        }
    }
}

struct ChatSessionDetailView: View {
    let sessionId: UUID
    @StateObject private var viewModel = ChatHistoryViewModel()

    var body: some View {
        Group {
            if viewModel.isLoadingDetail {
                ProgressView("Loading conversation...")
            } else if let session = viewModel.selectedSession {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        sessionHeader(session)

                        if !session.messages.isEmpty {
                            messagesSection(session.messages)
                        } else {
                            Text("No messages in this conversation.")
                                .foregroundColor(.secondary)
                                .padding()
                        }
                    }
                    .padding()
                }
            } else if let error = viewModel.error {
                VStack(spacing: 12) {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.largeTitle)
                        .foregroundColor(.orange)

                    Text("Failed to load conversation")
                        .font(.headline)

                    Text(error)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .multilineTextAlignment(.center)

                    Button("Try Again") {
                        Task {
                            await viewModel.loadSessionDetail(sessionId)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "bubble.left.and.bubble.right")
                        .font(.largeTitle)
                        .foregroundColor(.gray)

                    Text("Unable to load conversation")
                        .font(.headline)

                    Button("Try Again") {
                        Task {
                            await viewModel.loadSessionDetail(sessionId)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
            }
        }
        .navigationTitle("Conversation")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadSessionDetail(sessionId)
        }
    }

    private func sessionHeader(_ session: ChatSession) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(session.createdAt.formattedDateTime)
                    .font(.headline)

                Spacer()

                if let type = session.sessionType {
                    Text(displayName(for: type))
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.journalPrimary.opacity(0.1))
                        .cornerRadius(8)
                }
            }

            if let summary = session.summary, !summary.isEmpty {
                Text(summary)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }

            if let topics = session.keyTopics, !topics.isEmpty {
                HStack {
                    Image(systemName: "tag")
                        .font(.caption)
                        .foregroundColor(.journalPrimary)

                    Text(topics)
                        .font(.caption)
                        .foregroundColor(.journalPrimary)
                }
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(12)
    }

    private func messagesSection(_ messages: [ChatMessage]) -> some View {
        VStack(spacing: 12) {
            ForEach(messages.filter { $0.role != .system }) { message in
                MessageBubble(message: message)
            }
        }
    }

    private func displayName(for type: String) -> String {
        switch type {
        case "morning": return "Morning"
        case "evening": return "Evening"
        default: return "Freeform"
        }
    }
}

struct MessageBubble: View {
    let message: ChatMessage

    var isUser: Bool {
        message.role == .user
    }

    var body: some View {
        HStack {
            if isUser { Spacer(minLength: 60) }

            VStack(alignment: isUser ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .font(.body)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(isUser ? Color.journalPrimary : Color.gray.opacity(0.15))
                    .foregroundColor(isUser ? .white : .primary)
                    .cornerRadius(18)

                Text(message.createdAt.formattedTime)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if !isUser { Spacer(minLength: 60) }
        }
    }
}

#Preview {
    NavigationStack {
        ChatHistoryView()
    }
}
