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

            VoiceChatTabView()
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

struct VoiceChatTabView: View {
    @State private var showVoiceChat = false
    @State private var selectedJournalType: String? = nil

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.95, green: 0.95, blue: 0.98),
                        Color(red: 0.9, green: 0.92, blue: 0.98)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()

                VStack(spacing: 32) {
                    Spacer()

                    Image("BuddyNeutral")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 150, height: 150)
                        .clipShape(Circle())
                        .overlay(
                            Circle()
                                .stroke(
                                    LinearGradient(
                                        colors: [.journalPrimary, .journalSecondary],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ),
                                    lineWidth: 4
                                )
                        )
                        .shadow(color: .journalPrimary.opacity(0.3), radius: 20)

                    VStack(spacing: 8) {
                        Text("Talk with Buddy")
                            .font(.title)
                            .fontWeight(.bold)

                        Text("Your AI journaling companion is ready to listen")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }

                    VStack(spacing: 16) {
                        Button {
                            selectedJournalType = nil
                            showVoiceChat = true
                        } label: {
                            HStack {
                                Image(systemName: "mic.fill")
                                Text("Start Freeform Session")
                            }
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(
                                LinearGradient(
                                    colors: [.journalPrimary, .journalSecondary],
                                    startPoint: .leading,
                                    endPoint: .trailing
                                )
                            )
                            .cornerRadius(16)
                        }

                        HStack(spacing: 12) {
                            Button {
                                selectedJournalType = "morning"
                                showVoiceChat = true
                            } label: {
                                HStack {
                                    Image(systemName: "sunrise.fill")
                                        .foregroundColor(.orange)
                                    Text("Morning")
                                }
                                .font(.subheadline.weight(.medium))
                                .foregroundColor(.primary)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.white)
                                .cornerRadius(12)
                                .shadow(color: .black.opacity(0.05), radius: 5)
                            }

                            Button {
                                selectedJournalType = "evening"
                                showVoiceChat = true
                            } label: {
                                HStack {
                                    Image(systemName: "moon.stars.fill")
                                        .foregroundColor(.indigo)
                                    Text("Evening")
                                }
                                .font(.subheadline.weight(.medium))
                                .foregroundColor(.primary)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.white)
                                .cornerRadius(12)
                                .shadow(color: .black.opacity(0.05), radius: 5)
                            }
                        }
                    }
                    .padding(.horizontal, 24)

                    Spacer()
                    Spacer()
                }
            }
            .navigationTitle("Talk")
            .fullScreenCover(isPresented: $showVoiceChat) {
                VoiceChatView(journalType: selectedJournalType)
            }
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
