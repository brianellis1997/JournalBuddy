import SwiftUI

struct ContentView: View {
    @EnvironmentObject var authViewModel: AuthViewModel

    var body: some View {
        Group {
            if authViewModel.isAuthenticated {
                MainTabView()
            } else {
                LoginView(authViewModel: authViewModel)
            }
        }
        .animation(.easeInOut, value: authViewModel.isAuthenticated)
    }
}

struct MainTabView: View {
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house.fill")
                }
                .tag(0)

            JournalListView()
                .tabItem {
                    Label("Journal", systemImage: "book.fill")
                }
                .tag(1)

            VoiceChatPlaceholderView()
                .tabItem {
                    Label("Talk", systemImage: "waveform.circle.fill")
                }
                .tag(2)

            GoalsListView()
                .tabItem {
                    Label("Goals", systemImage: "target")
                }
                .tag(3)

            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person.fill")
                }
                .tag(4)
        }
        .tint(.journalPrimary)
    }
}

struct VoiceChatPlaceholderView: View {
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Image(systemName: "waveform.circle.fill")
                    .font(.system(size: 80))
                    .foregroundStyle(.linearGradient(
                        colors: [.journalPrimary, .journalSecondary],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ))

                Text("Voice Chat")
                    .font(.title)
                    .fontWeight(.bold)

                Text("Coming soon...")
                    .foregroundColor(.secondary)
            }
            .navigationTitle("Talk")
        }
    }
}

struct ProfileView: View {
    @EnvironmentObject var authViewModel: AuthViewModel

    var body: some View {
        NavigationStack {
            List {
                if let user = authViewModel.currentUser {
                    Section {
                        HStack {
                            Circle()
                                .fill(.linearGradient(
                                    colors: [.journalPrimary, .journalSecondary],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ))
                                .frame(width: 60, height: 60)
                                .overlay {
                                    Text(user.name.prefix(1).uppercased())
                                        .font(.title)
                                        .fontWeight(.bold)
                                        .foregroundColor(.white)
                                }

                            VStack(alignment: .leading, spacing: 4) {
                                Text(user.name)
                                    .font(.headline)
                                Text(user.email)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            .padding(.leading, 8)
                        }
                        .padding(.vertical, 8)
                    }

                    if let level = user.level, let xp = user.totalXP {
                        Section("Progress") {
                            HStack {
                                Label("Level", systemImage: "star.fill")
                                    .foregroundColor(.levelPurple)
                                Spacer()
                                Text("\(level)")
                                    .fontWeight(.semibold)
                            }

                            HStack {
                                Label("Total XP", systemImage: "bolt.fill")
                                    .foregroundColor(.xpGold)
                                Spacer()
                                Text("\(xp)")
                                    .fontWeight(.semibold)
                            }
                        }
                    }
                }

                Section {
                    Button(role: .destructive) {
                        Task {
                            await authViewModel.logout()
                        }
                    } label: {
                        HStack {
                            Spacer()
                            Text("Log Out")
                            Spacer()
                        }
                    }
                }
            }
            .navigationTitle("Profile")
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthViewModel())
}
