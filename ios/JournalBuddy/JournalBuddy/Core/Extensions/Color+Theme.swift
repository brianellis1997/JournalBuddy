import SwiftUI

extension Color {
    // Primary brand colors
    static let brandPrimary = Color("BrandPrimary", bundle: nil)
    static let brandSecondary = Color("BrandSecondary", bundle: nil)

    // Fallback colors if assets not defined
    static let journalPrimary = Color(red: 99/255, green: 102/255, blue: 241/255) // Indigo
    static let journalSecondary = Color(red: 139/255, green: 92/255, blue: 246/255) // Purple

    // Mood colors
    static let moodGreat = Color(red: 34/255, green: 197/255, blue: 94/255) // Green
    static let moodGood = Color(red: 132/255, green: 204/255, blue: 22/255) // Lime
    static let moodOkay = Color(red: 250/255, green: 204/255, blue: 21/255) // Yellow
    static let moodBad = Color(red: 249/255, green: 115/255, blue: 22/255) // Orange
    static let moodTerrible = Color(red: 239/255, green: 68/255, blue: 68/255) // Red

    // Status colors
    static let success = Color(red: 34/255, green: 197/255, blue: 94/255)
    static let warning = Color(red: 250/255, green: 204/255, blue: 21/255)
    static let error = Color(red: 239/255, green: 68/255, blue: 68/255)

    // XP and level colors
    static let xpGold = Color(red: 250/255, green: 204/255, blue: 21/255)
    static let levelPurple = Color(red: 139/255, green: 92/255, blue: 246/255)

    // Background variants
    static let cardBackground = Color(.systemBackground)
    static let secondaryBackground = Color(.secondarySystemBackground)
    static let tertiaryBackground = Color(.tertiarySystemBackground)
}

extension MoodType {
    var color: Color {
        switch self {
        case .great: return .moodGreat
        case .good: return .moodGood
        case .okay: return .moodOkay
        case .bad: return .moodBad
        case .terrible: return .moodTerrible
        }
    }
}

extension GoalStatus {
    var color: Color {
        switch self {
        case .active: return .journalPrimary
        case .completed: return .success
        case .paused: return .warning
        case .abandoned: return .error
        }
    }
}
