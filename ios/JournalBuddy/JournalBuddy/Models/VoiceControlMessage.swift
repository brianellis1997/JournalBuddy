import Foundation

enum VoiceMessageType: String, Codable {
    case connected
    case ready
    case userTranscript = "user_transcript"
    case interimTranscript = "interim_transcript"
    case assistantText = "assistant_text"
    case assistantThinking = "assistant_thinking"
    case assistantSpeaking = "assistant_speaking"
    case assistantDone = "assistant_done"
    case toolCall = "tool_call"
    case emotion
    case interrupted
    case conversationEnded = "conversation_ended"
    case ttsUnavailable = "tts_unavailable"
    case error
    case pong
}

struct VoiceControlMessage: Codable {
    let type: VoiceMessageType
    let data: VoiceMessageData?
}

struct VoiceMessageData: Codable {
    var userId: String?
    var text: String?
    var isFinal: Bool?
    var message: String?
    var tool: String?
    var status: String?
    var emotion: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case text
        case isFinal = "is_final"
        case message
        case tool
        case status
        case emotion
    }
}

struct VoiceSendMessage: Codable {
    let type: String
    var transcript: String?
}

enum AvatarEmotion: String, CaseIterable {
    case neutral
    case happy
    case warm
    case concerned
    case curious
    case encouraging
    case celebrating

    var eyebrowStyle: String {
        switch self {
        case .neutral: return "normal"
        case .happy, .encouraging, .warm, .celebrating: return "raised"
        case .concerned: return "furrowed"
        case .curious: return "one-raised"
        }
    }

    var mouthStyle: String {
        switch self {
        case .neutral, .curious: return "neutral"
        case .happy, .celebrating: return "smile"
        case .concerned: return "slight-frown"
        case .encouraging, .warm: return "warm-smile"
        }
    }
}

enum VoiceChatState {
    case disconnected
    case connecting
    case idle
    case listening
    case thinking
    case speaking

    var statusText: String {
        switch self {
        case .disconnected: return "Disconnected"
        case .connecting: return "Connecting..."
        case .idle: return "Ready"
        case .listening: return "Listening..."
        case .thinking: return "Thinking..."
        case .speaking: return "Speaking..."
        }
    }
}
