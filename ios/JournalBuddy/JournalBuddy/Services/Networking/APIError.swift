import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(statusCode: Int, message: String?)
    case decodingError(Error)
    case encodingError(Error)
    case networkError(Error)
    case unauthorized
    case tokenRefreshFailed
    case noData

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let statusCode, let message):
            if let message = message {
                return message
            }
            return "HTTP error: \(statusCode)"
        case .decodingError(let error):
            return "Failed to decode response: \(error.localizedDescription)"
        case .encodingError(let error):
            return "Failed to encode request: \(error.localizedDescription)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .unauthorized:
            return "Unauthorized - please log in again"
        case .tokenRefreshFailed:
            return "Session expired - please log in again"
        case .noData:
            return "No data received"
        }
    }

    var isAuthError: Bool {
        switch self {
        case .unauthorized, .tokenRefreshFailed:
            return true
        case .httpError(let statusCode, _):
            return statusCode == 401
        default:
            return false
        }
    }
}

struct APIErrorResponse: Codable {
    let detail: String?
}
