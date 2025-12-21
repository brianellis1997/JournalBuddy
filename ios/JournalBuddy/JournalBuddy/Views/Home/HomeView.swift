import SwiftUI

struct HomeView: View {
    @EnvironmentObject var authViewModel: AuthViewModel
    @StateObject private var viewModel = HomeViewModel()
    @State private var showVoiceChat = false
    @State private var voiceChatJournalType: String? = nil

    var body: some View {
        NavigationStack {
            ZStack {
                ScrollView {
                    VStack(spacing: 24) {
                        greetingSection

                        if viewModel.scheduleStatus != nil {
                            scheduleSection
                        }

                        statsSection

                        recentEntriesSection
                    }
                    .padding()
                    .padding(.bottom, 80)
                }

                voiceChatFAB
            }
            .navigationTitle("Home")
            .refreshable {
                await viewModel.refresh()
            }
            .task {
                await viewModel.loadData()
            }
            .fullScreenCover(isPresented: $showVoiceChat) {
                VoiceChatView(journalType: voiceChatJournalType)
            }
        }
    }

    private var voiceChatFAB: some View {
        VStack {
            Spacer()
            HStack {
                Spacer()
                Button {
                    voiceChatJournalType = nil
                    showVoiceChat = true
                } label: {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [.journalPrimary, .journalSecondary],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 60, height: 60)
                            .shadow(color: .journalPrimary.opacity(0.4), radius: 10, x: 0, y: 4)

                        Image(systemName: "mic.fill")
                            .font(.title2)
                            .foregroundColor(.white)
                    }
                }
                .padding(.trailing, 20)
                .padding(.bottom, 20)
            }
        }
    }

    private var greetingSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(greetingText)
                .font(.title2)
                .fontWeight(.bold)

            if let user = authViewModel.currentUser {
                Text("Welcome back, \(user.name.components(separatedBy: " ").first ?? user.name)!")
                    .foregroundColor(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var greetingText: String {
        let hour = Calendar.current.component(.hour, from: Date())
        if hour < 12 {
            return "Good morning"
        } else if hour < 17 {
            return "Good afternoon"
        } else {
            return "Good evening"
        }
    }

    private var scheduleSection: some View {
        VStack(spacing: 12) {
            if let status = viewModel.scheduleStatus {
                if status.shouldShowMorning && !status.morningCompleted {
                    SchedulePromptCard(
                        type: .morning,
                        prompt: status.morningPrompt ?? "Start your day with reflection"
                    ) {
                        voiceChatJournalType = "morning"
                        showVoiceChat = true
                    }
                }

                if status.shouldShowEvening && !status.eveningCompleted {
                    SchedulePromptCard(
                        type: .evening,
                        prompt: status.eveningPrompt ?? "Reflect on your day"
                    ) {
                        voiceChatJournalType = "evening"
                        showVoiceChat = true
                    }
                }

                if status.morningCompleted && status.shouldShowMorning {
                    completedCard(type: .morning)
                }

                if status.eveningCompleted && status.shouldShowEvening {
                    completedCard(type: .evening)
                }
            }
        }
    }

    private func completedCard(type: JournalType) -> some View {
        HStack {
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.success)

            Text("\(type.displayName) journal completed!")
                .font(.subheadline)

            Spacer()
        }
        .padding()
        .background(Color.success.opacity(0.1))
        .cornerRadius(12)
    }

    private var statsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Your Progress")
                .font(.headline)

            if let metrics = viewModel.metrics {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    StatCard(
                        title: "Current Streak",
                        value: "\(metrics.currentStreak)",
                        icon: "flame.fill",
                        color: .orange
                    )

                    StatCard(
                        title: "Total Entries",
                        value: "\(metrics.totalEntries)",
                        icon: "book.fill",
                        color: .journalPrimary
                    )

                    StatCard(
                        title: "Level",
                        value: "\(metrics.level)",
                        icon: "star.fill",
                        color: .levelPurple
                    )

                    StatCard(
                        title: "Total XP",
                        value: "\(metrics.totalXP)",
                        icon: "bolt.fill",
                        color: .xpGold
                    )
                }
            } else if viewModel.isLoading {
                ProgressView()
                    .frame(maxWidth: .infinity)
                    .padding()
            }
        }
    }

    private var recentEntriesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Recent Entries")
                    .font(.headline)

                Spacer()

                NavigationLink("See All") {
                    JournalListView()
                }
                .font(.subheadline)
                .foregroundColor(.journalPrimary)
            }

            if viewModel.recentEntries.isEmpty && !viewModel.isLoading {
                Text("No entries yet. Start journaling!")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding()
            } else {
                ForEach(viewModel.recentEntries.prefix(3)) { entry in
                    EntryRowCard(entry: entry)
                }
            }
        }
    }
}

struct SchedulePromptCard: View {
    let type: JournalType
    let prompt: String
    let onStart: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: type.icon)
                    .foregroundColor(.journalPrimary)

                Text("\(type.displayName) Journal")
                    .font(.headline)

                Spacer()
            }

            Text(prompt)
                .font(.subheadline)
                .foregroundColor(.secondary)

            Button(action: onStart) {
                HStack {
                    Image(systemName: "mic.fill")
                    Text("Start Voice Journal")
                }
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(
                    LinearGradient(
                        colors: [.journalPrimary, .journalSecondary],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .cornerRadius(10)
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }
}

struct StatCard: View {
    let title: String
    let value: String
    let icon: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(color)
                Spacer()
            }

            Text(value)
                .font(.title2)
                .fontWeight(.bold)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 3, x: 0, y: 1)
    }
}

struct EntryRowCard: View {
    let entry: Entry

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                if let mood = entry.mood {
                    Text(mood.emoji)
                }

                Text(entry.title ?? "Untitled")
                    .font(.subheadline)
                    .fontWeight(.medium)
                    .lineLimit(1)

                Spacer()

                Text(entry.createdAt.relativeString)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Text(entry.content)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.03), radius: 2, x: 0, y: 1)
    }
}

#Preview {
    HomeView()
        .environmentObject(AuthViewModel())
}
