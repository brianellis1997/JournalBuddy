import Foundation
import SwiftUI

@MainActor
class AuthViewModel: ObservableObject {
    @Published var currentUser: User?
    @Published var isAuthenticated = false
    @Published var isLoading = false
    @Published var error: String?

    @Published var email = ""
    @Published var password = ""
    @Published var name = ""
    @Published var confirmPassword = ""

    init() {
        Task {
            await checkAuthStatus()
        }
    }

    func checkAuthStatus() async {
        let hasToken = await KeychainManager.shared.isAuthenticated
        if hasToken {
            await fetchCurrentUser()
        }
    }

    func login() async {
        guard validateLoginInput() else { return }

        isLoading = true
        error = nil

        do {
            _ = try await APIClient.shared.login(email: email, password: password)
            await fetchCurrentUser()
            clearInputs()
        } catch let apiError as APIError {
            error = apiError.errorDescription
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func signup() async {
        guard validateSignupInput() else { return }

        isLoading = true
        error = nil

        do {
            _ = try await APIClient.shared.signup(email: email, password: password, name: name)
            _ = try await APIClient.shared.login(email: email, password: password)
            await fetchCurrentUser()
            clearInputs()
        } catch let apiError as APIError {
            error = apiError.errorDescription
        } catch {
            self.error = error.localizedDescription
        }

        isLoading = false
    }

    func logout() async {
        await APIClient.shared.logout()
        currentUser = nil
        isAuthenticated = false
        clearInputs()
    }

    private func fetchCurrentUser() async {
        do {
            currentUser = try await APIClient.shared.getCurrentUser()
            isAuthenticated = true
        } catch {
            await logout()
        }
    }

    private func validateLoginInput() -> Bool {
        if email.isEmpty {
            error = "Email is required"
            return false
        }
        if password.isEmpty {
            error = "Password is required"
            return false
        }
        if !email.contains("@") {
            error = "Please enter a valid email"
            return false
        }
        return true
    }

    private func validateSignupInput() -> Bool {
        if name.isEmpty {
            error = "Name is required"
            return false
        }
        if email.isEmpty {
            error = "Email is required"
            return false
        }
        if !email.contains("@") {
            error = "Please enter a valid email"
            return false
        }
        if password.isEmpty {
            error = "Password is required"
            return false
        }
        if password.count < 6 {
            error = "Password must be at least 6 characters"
            return false
        }
        if password != confirmPassword {
            error = "Passwords do not match"
            return false
        }
        return true
    }

    private func clearInputs() {
        email = ""
        password = ""
        name = ""
        confirmPassword = ""
    }
}
