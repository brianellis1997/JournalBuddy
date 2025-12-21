import SwiftUI

struct SignupView: View {
    @ObservedObject var authViewModel: AuthViewModel
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(spacing: 32) {
                headerSection

                inputSection

                if let error = authViewModel.error {
                    errorMessage(error)
                }

                signupButton

                loginLink
            }
            .padding(.horizontal, 24)
            .padding(.top, 40)
        }
        .navigationTitle("Create Account")
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(authViewModel.isLoading)
    }

    private var headerSection: some View {
        VStack(spacing: 12) {
            Image("BuddyHappy")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 100, height: 100)
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
                .shadow(color: .journalPrimary.opacity(0.3), radius: 10)

            Text("Join JournalBuddy")
                .font(.title2)
                .fontWeight(.bold)

            Text("Start your journaling journey today")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
    }

    private var inputSection: some View {
        VStack(spacing: 16) {
            TextField("Name", text: $authViewModel.name)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.name)
                .autocapitalization(.words)

            TextField("Email", text: $authViewModel.email)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.emailAddress)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .autocorrectionDisabled()

            SecureField("Password", text: $authViewModel.password)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.newPassword)

            SecureField("Confirm Password", text: $authViewModel.confirmPassword)
                .textFieldStyle(JBTextFieldStyle())
                .textContentType(.newPassword)
        }
    }

    private func errorMessage(_ message: String) -> some View {
        Text(message)
            .font(.footnote)
            .foregroundColor(.error)
            .multilineTextAlignment(.center)
            .padding(.horizontal)
    }

    private var signupButton: some View {
        Button {
            Task {
                await authViewModel.signup()
            }
        } label: {
            Group {
                if authViewModel.isLoading {
                    ProgressView()
                        .tint(.white)
                } else {
                    Text("Create Account")
                        .fontWeight(.semibold)
                }
            }
            .frame(maxWidth: .infinity)
            .frame(height: 50)
        }
        .buttonStyle(JBPrimaryButtonStyle())
        .disabled(authViewModel.isLoading)
    }

    private var loginLink: some View {
        HStack {
            Text("Already have an account?")
                .foregroundColor(.secondary)

            Button("Log In") {
                dismiss()
            }
            .foregroundColor(.journalPrimary)
            .fontWeight(.semibold)
        }
        .font(.subheadline)
    }
}

#Preview {
    NavigationStack {
        SignupView(authViewModel: AuthViewModel())
    }
}
