import Foundation

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let baseURL: URL
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    private var isRefreshing = false
    private var refreshContinuations: [CheckedContinuation<Void, Error>] = []

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
        self.baseURL = APIConstants.baseURL
        self.decoder = .apiDecoder
        self.encoder = .apiEncoder
    }

    // MARK: - Auth Endpoints

    func login(email: String, password: String) async throws -> Token {
        let body = LoginRequest(email: email, password: password)
        let formData = "username=\(email)&password=\(password)"
            .addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""

        var request = URLRequest(url: baseURL.appendingPathComponent(APIConstants.Endpoints.login))
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        request.httpBody = formData.data(using: .utf8)

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)

        let token = try decoder.decode(Token.self, from: data)
        try await KeychainManager.shared.saveTokens(access: token.accessToken, refresh: token.refreshToken)
        return token
    }

    func signup(email: String, password: String, name: String) async throws -> User {
        let body = SignupRequest(email: email, password: password, name: name)
        return try await request(
            endpoint: APIConstants.Endpoints.signup,
            method: "POST",
            body: body,
            requiresAuth: false
        )
    }

    func getCurrentUser() async throws -> User {
        return try await request(
            endpoint: APIConstants.Endpoints.me,
            method: "GET"
        )
    }

    func refreshToken() async throws {
        guard !isRefreshing else {
            try await withCheckedThrowingContinuation { continuation in
                refreshContinuations.append(continuation)
            }
            return
        }

        isRefreshing = true
        defer {
            isRefreshing = false
            refreshContinuations.forEach { $0.resume(returning: ()) }
            refreshContinuations.removeAll()
        }

        guard let refreshToken = await KeychainManager.shared.getRefreshToken() else {
            throw APIError.tokenRefreshFailed
        }

        var request = URLRequest(url: baseURL.appendingPathComponent(APIConstants.Endpoints.refresh))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(["refresh_token": refreshToken])

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 401 {
            await KeychainManager.shared.clearTokens()
            throw APIError.tokenRefreshFailed
        }

        try validateResponse(response, data: data)

        let token = try decoder.decode(Token.self, from: data)
        try await KeychainManager.shared.saveTokens(access: token.accessToken, refresh: token.refreshToken)
    }

    func logout() async {
        await KeychainManager.shared.clearTokens()
    }

    // MARK: - Entry Endpoints

    func getEntries(page: Int = 1, limit: Int = 20, journalType: JournalType? = nil) async throws -> EntryListResponse {
        var queryItems = [URLQueryItem(name: "page", value: "\(page)"),
                         URLQueryItem(name: "limit", value: "\(limit)")]
        if let journalType = journalType {
            queryItems.append(URLQueryItem(name: "journal_type", value: journalType.rawValue))
        }
        return try await request(
            endpoint: APIConstants.Endpoints.entries,
            method: "GET",
            queryItems: queryItems
        )
    }

    func getEntry(_ id: UUID) async throws -> Entry {
        return try await request(
            endpoint: APIConstants.Endpoints.entry(id),
            method: "GET"
        )
    }

    func createEntry(_ entry: EntryCreate) async throws -> Entry {
        return try await request(
            endpoint: APIConstants.Endpoints.entries,
            method: "POST",
            body: entry
        )
    }

    func updateEntry(_ id: UUID, _ update: EntryUpdate) async throws -> Entry {
        return try await request(
            endpoint: APIConstants.Endpoints.entry(id),
            method: "PATCH",
            body: update
        )
    }

    func deleteEntry(_ id: UUID) async throws {
        let _: EmptyResponse = try await request(
            endpoint: APIConstants.Endpoints.entry(id),
            method: "DELETE"
        )
    }

    // MARK: - Goal Endpoints

    func getGoals(status: GoalStatus? = nil) async throws -> [Goal] {
        var queryItems: [URLQueryItem] = []
        if let status = status {
            queryItems.append(URLQueryItem(name: "status_filter", value: status.rawValue))
        }
        return try await request(
            endpoint: APIConstants.Endpoints.goals,
            method: "GET",
            queryItems: queryItems
        )
    }

    func getGoal(_ id: UUID) async throws -> Goal {
        return try await request(
            endpoint: APIConstants.Endpoints.goal(id),
            method: "GET"
        )
    }

    func createGoal(_ goal: GoalCreate) async throws -> Goal {
        return try await request(
            endpoint: APIConstants.Endpoints.goals,
            method: "POST",
            body: goal
        )
    }

    func updateGoal(_ id: UUID, _ update: GoalUpdate) async throws -> Goal {
        return try await request(
            endpoint: APIConstants.Endpoints.goal(id),
            method: "PATCH",
            body: update
        )
    }

    func deleteGoal(_ id: UUID) async throws {
        let _: EmptyResponse = try await request(
            endpoint: APIConstants.Endpoints.goal(id),
            method: "DELETE"
        )
    }

    // MARK: - Gamification Endpoints

    func getGamificationStats() async throws -> GamificationStats {
        return try await request(
            endpoint: APIConstants.Endpoints.gamificationStats,
            method: "GET"
        )
    }

    func getMetrics() async throws -> Metrics {
        return try await request(
            endpoint: APIConstants.Endpoints.metrics,
            method: "GET"
        )
    }

    func getScheduleStatus() async throws -> ScheduleStatus {
        return try await request(
            endpoint: APIConstants.Endpoints.scheduleStatus,
            method: "GET"
        )
    }

    // MARK: - Summary Endpoints

    func getSummaries() async throws -> AutoSummaryListResponse {
        return try await request(
            endpoint: APIConstants.Endpoints.summaries,
            method: "GET"
        )
    }

    func generateWeeklySummary() async throws -> GenerateSummaryResponse {
        return try await request(
            endpoint: APIConstants.Endpoints.weeklySummary,
            method: "POST"
        )
    }

    // MARK: - Generic Request

    private func request<T: Decodable>(
        endpoint: String,
        method: String,
        body: Encodable? = nil,
        queryItems: [URLQueryItem] = [],
        requiresAuth: Bool = true
    ) async throws -> T {
        var urlComponents = URLComponents(url: baseURL.appendingPathComponent(endpoint), resolvingAgainstBaseURL: true)!
        if !queryItems.isEmpty {
            urlComponents.queryItems = queryItems
        }

        guard let url = urlComponents.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if requiresAuth {
            if let accessToken = await KeychainManager.shared.getAccessToken() {
                request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
            }
        }

        if let body = body {
            request.httpBody = try encoder.encode(body)
        }

        do {
            let (data, response) = try await session.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }

            if httpResponse.statusCode == 401 && requiresAuth {
                try await refreshToken()
                return try await self.request(
                    endpoint: endpoint,
                    method: method,
                    body: body,
                    queryItems: queryItems,
                    requiresAuth: requiresAuth
                )
            }

            try validateResponse(response, data: data)

            if T.self == EmptyResponse.self {
                return EmptyResponse() as! T
            }

            return try decoder.decode(T.self, from: data)
        } catch let error as APIError {
            throw error
        } catch let error as DecodingError {
            throw APIError.decodingError(error)
        } catch {
            throw APIError.networkError(error)
        }
    }

    private func validateResponse(_ response: URLResponse, data: Data) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            let message = try? decoder.decode(APIErrorResponse.self, from: data).detail
            throw APIError.httpError(statusCode: httpResponse.statusCode, message: message)
        }
    }
}

struct EmptyResponse: Decodable {}
