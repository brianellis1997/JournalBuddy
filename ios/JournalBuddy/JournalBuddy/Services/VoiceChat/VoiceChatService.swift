import Foundation

protocol VoiceChatServiceDelegate: AnyObject {
    func voiceChatDidChangeState(_ state: VoiceChatState)
    func voiceChatDidReceiveTranscript(_ text: String, isFinal: Bool, isUser: Bool)
    func voiceChatDidReceiveAssistantText(_ text: String)
    func voiceChatDidReceiveEmotion(_ emotion: AvatarEmotion)
    func voiceChatDidEnd(entryId: UUID?)
    func voiceChatDidError(_ message: String)
    func voiceChatDidUpdateAudioPlaying(_ isPlaying: Bool)
    func voiceChatDidUpdateMuted(_ isMuted: Bool)
    func voiceChatWillStartAssistantResponse()
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

    private(set) var isAudioPlaying: Bool = false {
        didSet {
            if oldValue != isAudioPlaying {
                delegate?.voiceChatDidUpdateAudioPlaying(isAudioPlaying)
            }
        }
    }

    private(set) var isMuted: Bool = false

    private var pingTimer: Timer?
    private var thinkingTimeoutTimer: Timer?
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
        thinkingTimeoutTimer?.invalidate()
        thinkingTimeoutTimer = nil
        isAudioPlaying = false
        isMuted = false
        state = .disconnected
    }

    func startRecording() {
        guard state == .idle || state == .speaking || state == .thinking else {
            print("[VoiceChat] Cannot start recording in state: \(state)")
            return
        }

        guard webSocketManager.isConnected else {
            print("[VoiceChat] WebSocket not connected, cannot record")
            delegate?.voiceChatDidError("Connection lost. Please try again.")
            state = .disconnected
            return
        }

        thinkingTimeoutTimer?.invalidate()
        thinkingTimeoutTimer = nil

        if state == .speaking {
            webSocketManager.sendInterrupt()
            audioEngine.stopPlayback()
            isAudioPlaying = false
        }

        if state == .thinking {
            print("[VoiceChat] Resetting from thinking state to record again")
        }

        audioEngine.startRecording()
        state = .listening
        print("[VoiceChat] Started recording, state is now: \(state)")
    }

    func stopRecording() {
        guard state == .listening else { return }
        audioEngine.stopRecording()
        state = .thinking
        startThinkingTimeout()
    }

    private func startThinkingTimeout() {
        thinkingTimeoutTimer?.invalidate()
        thinkingTimeoutTimer = Timer.scheduledTimer(withTimeInterval: 30.0, repeats: false) { [weak self] _ in
            guard let self = self else { return }
            if self.state == .thinking {
                print("[VoiceChat] Thinking timeout - returning to idle")
                self.state = .idle
            }
        }
    }

    private func cancelThinkingTimeout() {
        thinkingTimeoutTimer?.invalidate()
        thinkingTimeoutTimer = nil
    }

    func interrupt() {
        if state == .speaking {
            webSocketManager.sendInterrupt()
            audioEngine.stopPlayback()
            isAudioPlaying = false
            state = .listening
        }
    }

    func toggleMute() {
        isMuted = !isMuted
        delegate?.voiceChatDidUpdateMuted(isMuted)

        if isMuted {
            audioEngine.stopRecording()
            if state == .listening {
                state = .idle
            }
        } else {
            startContinuousListening()
        }
    }

    private func startContinuousListening() {
        print("[VoiceChat] startContinuousListening called, state: \(state), connected: \(webSocketManager.isConnected), muted: \(isMuted)")

        guard webSocketManager.isConnected else {
            print("[VoiceChat] Cannot start listening - not connected")
            return
        }

        guard !isMuted else {
            print("[VoiceChat] Cannot start listening - muted")
            return
        }

        guard state != .speaking else {
            print("[VoiceChat] Cannot start listening - currently speaking")
            return
        }

        guard state != .disconnected else {
            print("[VoiceChat] Cannot start listening - disconnected")
            return
        }

        audioEngine.startRecording()
        state = .listening
        print("[VoiceChat] Continuous listening started")
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

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            self?.startContinuousListening()
        }
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
            delegate?.voiceChatWillStartAssistantResponse()
            state = .thinking

        case .assistantSpeaking:
            cancelThinkingTimeout()
            state = .speaking

        case .assistantDone:
            audioEngine.flushAudioBuffer()

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
            isAudioPlaying = false
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
        cancelThinkingTimeout()

        if state == .listening {
            print("[VoiceChat] Received audio while listening - stopping recording first")
            audioEngine.stopRecording()
        }

        audioEngine.playAudio(data)
        if state != .speaking {
            state = .speaking
        }
    }
}

extension VoiceChatService: AudioEngineDelegate {
    func audioEngineDidCaptureAudio(_ data: Data) {
        guard state == .listening && !isMuted else {
            return
        }
        webSocketManager.sendAudio(data)
    }

    func audioEngineDidStartPlaying() {
        print("[VoiceChat] Audio playback started")
        isAudioPlaying = true
        cancelThinkingTimeout()
        if state != .speaking {
            state = .speaking
        }
    }

    func audioEngineDidStopPlaying() {
        print("[VoiceChat] Audio playback finished")
        isAudioPlaying = false
        if state == .speaking {
            state = .idle
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            self?.startContinuousListening()
        }
    }
}
