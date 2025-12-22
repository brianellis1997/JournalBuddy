import SwiftUI

struct GamificationDashboardView: View {
    @StateObject private var viewModel = GamificationViewModel()

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                if let stats = viewModel.stats {
                    levelSection(stats)
                    streakSection(stats)
                    xpHistorySection(stats)
                    achievementsSection
                } else if viewModel.isLoading {
                    ProgressView("Loading...")
                        .frame(maxWidth: .infinity, minHeight: 200)
                } else if let error = viewModel.error {
                    errorView(error)
                }
            }
            .padding()
        }
        .navigationTitle("Progress")
        .refreshable {
            await viewModel.refresh()
        }
        .task {
            await viewModel.loadStats()
        }
    }

    private func levelSection(_ stats: GamificationStats) -> some View {
        VStack(spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Level \(stats.level)")
                        .font(.title)
                        .fontWeight(.bold)

                    Text("\(stats.totalXP) XP Total")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Spacer()

                ZStack {
                    Circle()
                        .stroke(Color.levelPurple.opacity(0.2), lineWidth: 8)
                        .frame(width: 80, height: 80)

                    Circle()
                        .trim(from: 0, to: viewModel.levelProgress)
                        .stroke(
                            LinearGradient(
                                colors: [.levelPurple, .journalSecondary],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            style: StrokeStyle(lineWidth: 8, lineCap: .round)
                        )
                        .frame(width: 80, height: 80)
                        .rotationEffect(.degrees(-90))

                    VStack(spacing: 0) {
                        Image(systemName: "star.fill")
                            .foregroundColor(.levelPurple)
                        Text("\(stats.level)")
                            .font(.headline)
                            .fontWeight(.bold)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Progress to Level \(stats.level + 1)")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    Text("\(stats.xpProgressInLevel) / \(stats.xpForNextLevel) XP")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                GeometryReader { geometry in
                    ZStack(alignment: .leading) {
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.levelPurple.opacity(0.2))
                            .frame(height: 12)

                        RoundedRectangle(cornerRadius: 6)
                            .fill(
                                LinearGradient(
                                    colors: [.levelPurple, .journalSecondary],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .frame(width: geometry.size.width * viewModel.levelProgress, height: 12)
                    }
                }
                .frame(height: 12)
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    private func streakSection(_ stats: GamificationStats) -> some View {
        HStack(spacing: 16) {
            StreakCard(
                title: "Current Streak",
                value: stats.currentStreak,
                icon: "flame.fill",
                color: .orange
            )

            StreakCard(
                title: "Longest Streak",
                value: stats.longestStreak,
                icon: "trophy.fill",
                color: .yellow
            )
        }
    }

    private func xpHistorySection(_ stats: GamificationStats) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Recent XP")
                .font(.headline)

            if stats.recentXPEvents.isEmpty {
                Text("No XP earned yet. Start journaling!")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity)
                    .padding()
            } else {
                ForEach(stats.recentXPEvents.prefix(5)) { event in
                    XPEventRow(event: event)
                }
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    private var achievementsSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Achievements")
                .font(.headline)

            if viewModel.unlockedAchievements.isEmpty && viewModel.lockedAchievements.isEmpty {
                Text("No achievements yet.")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            } else {
                if !viewModel.unlockedAchievements.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Unlocked")
                            .font(.subheadline)
                            .foregroundColor(.secondary)

                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 12) {
                            ForEach(viewModel.unlockedAchievements) { achievement in
                                AchievementCard(achievement: achievement, isUnlocked: true)
                            }
                        }
                    }
                }

                if !viewModel.lockedAchievements.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Locked")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .padding(.top, 8)

                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 12) {
                            ForEach(viewModel.lockedAchievements) { achievement in
                                AchievementCard(achievement: achievement, isUnlocked: false)
                            }
                        }
                    }
                }
            }
        }
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, x: 0, y: 2)
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundColor(.orange)

            Text("Failed to load progress")
                .font(.headline)

            Text(message)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button("Try Again") {
                Task {
                    await viewModel.loadStats()
                }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(maxWidth: .infinity)
    }
}

struct StreakCard: View {
    let title: String
    let value: Int
    let icon: String
    let color: Color

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title)
                .foregroundColor(color)

            Text("\(value)")
                .font(.title2)
                .fontWeight(.bold)

            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color.cardBackground)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.05), radius: 3, x: 0, y: 1)
    }
}

struct XPEventRow: View {
    let event: XPEvent

    var body: some View {
        HStack {
            Image(systemName: iconForEventType(event.eventType))
                .foregroundColor(.xpGold)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(displayNameForEventType(event.eventType))
                    .font(.subheadline)

                Text(event.createdAt.relativeString)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            Text("+\(event.xpAmount) XP")
                .font(.subheadline)
                .fontWeight(.semibold)
                .foregroundColor(.xpGold)
        }
        .padding(.vertical, 4)
    }

    private func iconForEventType(_ type: String) -> String {
        switch type {
        case "entry_created": return "book.fill"
        case "morning_journal": return "sunrise.fill"
        case "evening_journal": return "moon.stars.fill"
        case "goal_completed": return "target"
        case "streak_7": return "flame.fill"
        case "streak_30": return "flame.circle.fill"
        default: return "bolt.fill"
        }
    }

    private func displayNameForEventType(_ type: String) -> String {
        switch type {
        case "entry_created": return "Journal Entry"
        case "morning_journal": return "Morning Journal"
        case "evening_journal": return "Evening Journal"
        case "goal_completed": return "Goal Completed"
        case "streak_7": return "7-Day Streak Bonus"
        case "streak_30": return "30-Day Streak Bonus"
        default: return type.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
}

struct AchievementCard: View {
    let achievement: Achievement
    let isUnlocked: Bool

    var body: some View {
        VStack(spacing: 8) {
            Text(achievement.icon)
                .font(.largeTitle)
                .opacity(isUnlocked ? 1 : 0.4)

            Text(achievement.name)
                .font(.caption)
                .fontWeight(.medium)
                .multilineTextAlignment(.center)
                .lineLimit(2)

            if !isUnlocked, let progress = achievement.progress, let target = achievement.target {
                Text("\(progress)/\(target)")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(isUnlocked ? Color.xpGold.opacity(0.1) : Color.gray.opacity(0.1))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(isUnlocked ? Color.xpGold.opacity(0.3) : Color.clear, lineWidth: 1)
        )
    }
}

#Preview {
    NavigationStack {
        GamificationDashboardView()
    }
}
