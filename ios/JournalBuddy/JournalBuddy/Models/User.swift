import Foundation

struct User: Codable, Identifiable {
    let id: UUID
    let email: String
    let name: String
    var totalXP: Int?
    var level: Int?
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id, email, name
        case totalXP = "total_xp"
        case level
        case createdAt = "created_at"
    }
}

struct Token: Codable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
    }
}

struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct SignupRequest: Codable {
    let email: String
    let password: String
    let name: String
}
