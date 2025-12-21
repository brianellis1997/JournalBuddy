import SwiftUI

struct LoginView: View {
    @ObservedObject var authViewModel: AuthViewModel
    @State private var showSignup = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 32) {
                    headerSection

                    inputSection

                    if let error = authViewModel.error {
                        errorMessage(error)
                    }

                    loginButton

                    signupLink
                }
                .padding(.horizontal, 24)
                .padding(.top, 60)
            }
            .navigationDestination(isPresented: $showSignup) {
                SignupView(authViewModel: authViewModel)
            }
        }
    }

    private var headerSection: some View {
        VStack(spacing: 12) {
            Image("BuddyNeutral")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 120, height: 120)
                .clipShape(Circle())
                .overlay(
                    Circle()
                        .stroke(
                            LinearGradient(
                                colors: [.journalPrimary, .journalSecondary],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            ),
                            lineWidth: 3
                        )
                )
                .shadow(color: .journalPrimary.opacity(0.3), radius: 15)

            Text("JournalBuddy")
                .font(.largeTitle)
                .fontWeight(.bold)

            Text("Your AI journaling companion")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }

    private var inputSection: some View {
        VStack(spacing: 16) {
            TextField("Email", text: $authViewModel.email)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.emailAddress)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .autocorrectionDisabled()

            SecureField("Password", text: $authViewModel.password)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.password)
        }
    }

    private func errorMessage(_ message: String) -> some View {
        Text(message)
            .font(.footnote)
            .foregroundColor(.error)
            .multilineTextAlignment(.center)
            .padding(.horizontal)
    }

    private var loginButton: some View {
        Button {
            Task {
                await authViewModel.login()
            }
        } label: {
            Group {
                if authViewModel.isLoading {
                    ProgressView()
                        .tint(.white)
                } else {
                    Text("Log In")
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: 50)
        }
        .buttonStyle(JBPrimaryButtonStyle())
        .disabled(authViewModel.isLoading)
    }

    private var signupLink: some View {
        HStack {
            Text("Don't have an account?")
                .foregroundColor(.secondary)

            Button("Sign Up") {
                showSignup = true
            }
            .foregroundColor(.journalPrimary)
            .fontWeight(.semibold)
        }
        .font(.subheadline)
    }
}

struct JBTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(Color.secondaryBackground)
            .cornerRadius(12)
    }
}

struct JBPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .foregroundColor(.white)
            .background(
                LinearGradient(
                    colors: [.journalPrimary, .journalSecondary],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .cornerRadius(12)
            .opacity(configuration.isPressed ? 0.8 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

#Preview {
    LoginView(authViewModel: AuthViewModel())
}
