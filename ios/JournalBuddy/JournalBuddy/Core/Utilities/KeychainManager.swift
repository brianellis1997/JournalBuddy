import Foundation
import Security

actor KeychainManager {
    static let shared = KeychainManager()

    private let service = "com.journalbuddy.app"

    private enum Keys {
        static let accessToken = "access_token"
        static let refreshToken = "refresh_token"
    }

    private init() {}

    // MARK: - Token Management

    func saveTokens(access: String, refresh: String) throws {
        try save(key: Keys.accessToken, value: access)
        try save(key: Keys.refreshToken, value: refresh)
    }

    func getAccessToken() -> String? {
        return get(key: Keys.accessToken)
    }

    func getRefreshToken() -> String? {
        return get(key: Keys.refreshToken)
    }

    func clearTokens() {
        delete(key: Keys.accessToken)
        delete(key: Keys.refreshToken)
    }

    var isAuthenticated: Bool {
        getAccessToken() != nil
    }

    // MARK: - Generic Keychain Operations

    private func save(key: String, value: String) throws {
        guard let data = value.data(using: .utf8) else {
            throw KeychainError.encodingFailed
        }

        delete(key: key)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]

        let status = SecItemAdd(query as CFDictionary, nil)

        guard status == errSecSuccess else {
            throw KeychainError.saveFailed(status)
        }
    }

    private func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }

        return value
    }

    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]

        SecItemDelete(query as CFDictionary)
    }
}

enum KeychainError: LocalizedError {
    case encodingFailed
    case saveFailed(OSStatus)
    case notFound

    var errorDescription: String? {
        switch self {
        case .encodingFailed:
            return "Failed to encode data for keychain"
        case .saveFailed(let status):
            return "Failed to save to keychain: \(status)"
        case .notFound:
            return "Item not found in keychain"
        }
    }
}
