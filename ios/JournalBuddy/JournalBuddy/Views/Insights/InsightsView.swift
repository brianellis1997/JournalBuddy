import SwiftUI

struct InsightsView: View {
    @StateObject private var viewModel = InsightsViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                if viewModel.isLoading {
                    loadingView
                } else if let error = viewModel.error {
                    errorView(error)
                } else if !viewModel.hasData {
                    emptyStateView
                } else {
                    insightsContent
                }
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Insights")
            .refreshable {
                await viewModel.loadInsights()
            }
        }
        .task {
            await viewModel.loadInsights()
        }
    }

    private var loadingView: some View {
        VStack(spacing: 16) {
            ProgressView()
                .scaleEffect(1.5)
            Text("Loading insights...")
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 300)
    }

    private func errorView(_ error: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundColor(.orange)
            Text("Failed to load insights")
                .font(.headline)
            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            Button("Try Again") {
                Task { await viewModel.loadInsights() }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .frame(maxWidth: .infinity, minHeight: 300)
    }

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "chart.bar.doc.horizontal")
                .font(.system(size: 64))
                .foregroundColor(.journalPrimary.opacity(0.5))
            Text("No insights yet")
                .font(.headline)
            Text("Start journaling to see your mood trends, patterns, and themes.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding(40)
        .frame(maxWidth: .infinity, minHeight: 300)
    }

    private var insightsContent: some View {
        VStack(spacing: 20) {
            streakCard
            moodOverviewCard
            moodDistributionCard
            dayPatternsCard
            themesCard
            journalTypesCard
        }
        .padding()
    }

    private var streakCard: some View {
        HStack(spacing: 20) {
            streakStat(
                value: "\(viewModel.summary?.streak.currentStreak ?? 0)",
                label: "Current Streak",
                icon: "flame.fill",
                color: .orange
            )
            Divider()
            streakStat(
                value: "\(viewModel.summary?.streak.longestStreak ?? 0)",
                label: "Longest Streak",
                icon: "trophy.fill",
                color: .yellow
            )
            Divider()
            streakStat(
                value: "\(viewModel.summary?.streak.totalDays ?? 0)",
                label: "Total Days",
                icon: "calendar",
                color: .blue
            )
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private func streakStat(value: String, label: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(color)
            Text(value)
                .font(.title2)
                .fontWeight(.bold)
            Text(label)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private var moodOverviewCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Overall Mood")
                .font(.headline)

            HStack(spacing: 20) {
                Text(viewModel.moodEmoji)
                    .font(.system(size: 64))

                VStack(alignment: .leading, spacing: 4) {
                    Text(viewModel.moodDescription)
                        .font(.title2)
                        .fontWeight(.semibold)

                    if let avgScore = viewModel.summary?.moodTrends.averageMoodScore {
                        Text("Average: \(String(format: "%.1f", avgScore))/5")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }

                    Text("Last \(viewModel.summary?.moodTrends.periodDays ?? 30) days")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private var moodDistributionCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Mood Distribution")
                .font(.headline)

            VStack(spacing: 8) {
                ForEach(viewModel.sortedMoodDistribution, id: \.mood) { item in
                    HStack {
                        Text(viewModel.moodEmoji(for: item.mood))
                        Text(item.mood.capitalized)
                            .font(.subheadline)
                            .frame(width: 60, alignment: .leading)

                        GeometryReader { geometry in
                            ZStack(alignment: .leading) {
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(Color(.systemGray5))
                                RoundedRectangle(cornerRadius: 4)
                                    .fill(viewModel.moodColor(for: item.mood))
                                    .frame(width: geometry.size.width * item.percentage)
                            }
                        }
                        .frame(height: 20)

                        Text("\(item.count)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .frame(width: 30, alignment: .trailing)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private var dayPatternsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Best & Worst Days")
                .font(.headline)

            if let patterns = viewModel.summary?.dayPatterns {
                if !patterns.insights.isEmpty {
                    ForEach(patterns.insights, id: \.self) { insight in
                        HStack(alignment: .top, spacing: 8) {
                            Image(systemName: "lightbulb.fill")
                                .foregroundColor(.yellow)
                                .font(.caption)
                            Text(insight)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                    }
                } else {
                    Text("Journal more to see day-of-week patterns")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }

                Divider()

                HStack(spacing: 4) {
                    ForEach(patterns.patterns.sorted(by: { $0.dayNumber < $1.dayNumber })) { pattern in
                        VStack(spacing: 4) {
                            Text(String(pattern.day.prefix(1)))
                                .font(.caption2)
                                .foregroundColor(.secondary)
                            Circle()
                                .fill(dayPatternColor(pattern.avgMoodScore))
                                .frame(width: 32, height: 32)
                                .overlay(
                                    Text("\(pattern.entries)")
                                        .font(.caption2)
                                        .foregroundColor(.white)
                                )
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private func dayPatternColor(_ score: Double?) -> Color {
        guard let score = score else { return .gray }
        switch score {
        case 4...: return .green
        case 3..<4: return .mint
        case 2..<3: return .yellow
        default: return .orange
        }
    }

    private var themesCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Common Themes")
                .font(.headline)

            if viewModel.topThemes.isEmpty {
                Text("Write more entries to see common themes")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            } else {
                FlowLayout(spacing: 8) {
                    ForEach(viewModel.topThemes) { theme in
                        HStack(spacing: 4) {
                            Text(theme.word)
                                .font(.subheadline)
                            Text("(\(theme.count))")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 6)
                        .background(Color.journalPrimary.opacity(0.1))
                        .foregroundColor(.journalPrimary)
                        .cornerRadius(16)
                    }
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private var journalTypesCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Journal Types")
                .font(.headline)

            if let breakdown = viewModel.summary?.journalTypes.breakdown, !breakdown.isEmpty {
                HStack(spacing: 16) {
                    ForEach(breakdown) { stats in
                        VStack(spacing: 8) {
                            Image(systemName: journalTypeIcon(stats.type))
                                .font(.title2)
                                .foregroundColor(journalTypeColor(stats.type))
                            Text("\(stats.count)")
                                .font(.title3)
                                .fontWeight(.bold)
                            Text(stats.type.capitalized)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
            } else {
                Text("No journal type data yet")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
    }

    private func journalTypeIcon(_ type: String) -> String {
        switch type.lowercased() {
        case "morning": return "sunrise.fill"
        case "evening": return "moon.stars.fill"
        case "freeform": return "square.and.pencil"
        default: return "doc.text"
        }
    }

    private func journalTypeColor(_ type: String) -> Color {
        switch type.lowercased() {
        case "morning": return .orange
        case "evening": return .indigo
        case "freeform": return .journalPrimary
        default: return .gray
        }
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = FlowResult(
            in: proposal.replacingUnspecifiedDimensions().width,
            subviews: subviews,
            spacing: spacing
        )
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = FlowResult(
            in: bounds.width,
            subviews: subviews,
            spacing: spacing
        )
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x,
                                      y: bounds.minY + result.positions[index].y),
                         proposal: .unspecified)
        }
    }

    struct FlowResult {
        var size: CGSize = .zero
        var positions: [CGPoint] = []

        init(in maxWidth: CGFloat, subviews: Subviews, spacing: CGFloat) {
            var x: CGFloat = 0
            var y: CGFloat = 0
            var rowHeight: CGFloat = 0

            for subview in subviews {
                let size = subview.sizeThatFits(.unspecified)
                if x + size.width > maxWidth && x > 0 {
                    x = 0
                    y += rowHeight + spacing
                    rowHeight = 0
                }
                positions.append(CGPoint(x: x, y: y))
                rowHeight = max(rowHeight, size.height)
                x += size.width + spacing
                self.size.width = max(self.size.width, x)
            }
            self.size.height = y + rowHeight
        }
    }
}

#Preview {
    InsightsView()
}
