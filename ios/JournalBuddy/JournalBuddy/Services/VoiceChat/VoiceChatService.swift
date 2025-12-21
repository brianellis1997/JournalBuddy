import Foundation

protocol VoiceChatServiceDelegate: AnyObject {
    func voiceChatDidChangeState(_ state: VoiceChatState)
    func voiceChatDidReceiveTranscript(_ text: String, isFinal: Bool, isUser: Bool)
    func voiceChatDidReceiveAssistantText(_ text: String)
    func voiceChatDidReceiveEmotion(_ emotion: AvatarEmotion)
    func voiceChatDidEnd(entryId: UUID?)
    func voiceChatDidError(_ message: String)
}

class VoiceChatService: NSObject {
    weak var delegate: VoiceChatServiceDelegate?

    private let webSocketManager = WebSocketManager()
    private let audioEngine = AudioEngineManager()

    private(set) var state: VoiceChatState = .disconnected {
        didSet {
            if oldValue != state {
                delegate?.voiceChatDidChangeState(state)
            }
        }
    }

    private var pingTimer: Timer?
    private var token: String?
    private var createdEntryId: UUID?

    override init() {
        super.init()
        webSocketManager.delegate = self
        audioEngine.delegate = self
    }

    func start(token: String, journalType: String? = nil) {
        self.token = token
        state = .connecting
        webSocketManager.connect(token: token, journalType: journalType)
    }

    func stop() {
        stopRecording()
        audioEngine.reset()
        webSocketManager.disconnect()
        pingTimer?.invalidate()
        pingTimer = nil
        state = .disconnected
    }

    func startRecording() {
        guard state == .idle || state == .speaking else { return }

        if state == .speaking {
            webSocketManager.sendInterrupt()
            audioEngine.stopPlayback()
        }

        audioEngine.startRecording()
        state = .listening
    }

    func stopRecording() {
        guard state == .listening else { return }
        audioEngine.stopRecording()
        state = .thinking
    }

    func interrupt() {
        if state == .speaking {
            webSocketManager.sendInterrupt()
            audioEngine.stopPlayback()
            state = .idle
        }
    }

    private func startPingTimer() {
        pingTimer?.invalidate()
        pingTimer = Timer.scheduledTimer(withTimeInterval: 25, repeats: true) { [weak self] _ in
            self?.webSocketManager.sendPing()
        }
    }
}

extension VoiceChatService: WebSocketManagerDelegate {
    func webSocketDidConnect() {
        print("[VoiceChat] WebSocket connected")
        state = .idle
        startPingTimer()
    }

    func webSocketDidDisconnect(error: Error?) {
        print("[VoiceChat] WebSocket disconnected: \(error?.localizedDescription ?? "no error")")
        pingTimer?.invalidate()
        pingTimer = nil
        audioEngine.reset()
        state = .disconnected

        if let error = error {
            delegate?.voiceChatDidError("Connection lost: \(error.localizedDescription)")
        }
    }

    func webSocketDidReceiveMessage(_ message: VoiceControlMessage) {
        switch message.type {
        case .ready:
            state = .idle

        case .userTranscript:
            if let text = message.data?.text, let isFinal = message.data?.isFinal {
                delegate?.voiceChatDidReceiveTranscript(text, isFinal: isFinal, isUser: true)
            }

        case .interimTranscript:
            if let text = message.data?.text {
                delegate?.voiceChatDidReceiveTranscript(text, isFinal: false, isUser: true)
            }

        case .assistantText:
            if let text = message.data?.text {
                delegate?.voiceChatDidReceiveAssistantText(text)
            }

        case .assistantThinking:
            state = .thinking

        case .assistantSpeaking:
            state = .speaking

        case .assistantDone:
            state = .idle

        case .toolCall:
            if let tool = message.data?.tool {
                print("[VoiceChat] Tool called: \(tool)")
                if tool == "create_journal_entry" || tool == "end_conversation" {
                    if let entryIdString = message.data?.message,
                       let entryId = UUID(uuidString: entryIdString) {
                        createdEntryId = entryId
                    }
                }
            }

        case .emotion:
            if let emotionStr = message.data?.emotion,
               let emotion = AvatarEmotion(rawValue: emotionStr) {
                delegate?.voiceChatDidReceiveEmotion(emotion)
            }

        case .interrupted:
            audioEngine.stopPlayback()
            state = .idle

        case .conversationEnded:
            delegate?.voiceChatDidEnd(entryId: createdEntryId)
            stop()

        case .error:
            if let errorMsg = message.data?.message {
                delegate?.voiceChatDidError(errorMsg)
            }

        case .connected, .pong:
            break
        }
    }

    func webSocketDidReceiveAudio(_ data: Data) {
        audioEngine.playAudio(data)
        if state != .speaking {
            state = .speaking
        }
    }
}

extension VoiceChatService: AudioEngineDelegate {
    func audioEngineDidCaptureAudio(_ data: Data) {
        print("[VoiceChat] Received \(data.count) bytes from audio engine, sending to WebSocket")
        webSocketManager.sendAudio(data)
    }
}
