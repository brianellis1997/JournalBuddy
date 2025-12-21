import Foundation

protocol WebSocketManagerDelegate: AnyObject {
    func webSocketDidConnect()
    func webSocketDidDisconnect(error: Error?)
    func webSocketDidReceiveMessage(_ message: VoiceControlMessage)
    func webSocketDidReceiveAudio(_ data: Data)
}

class WebSocketManager: NSObject {
    weak var delegate: WebSocketManagerDelegate?

    private var webSocket: URLSessionWebSocketTask?
    private var session: URLSession!
    private(set) var isConnected = false

    override init() {
        super.init()
        session = URLSession(configuration: .default, delegate: self, delegateQueue: .main)
    }

    func connect(token: String, journalType: String? = nil) {
        var urlString = "\(APIConstants.wsBaseURL)\(APIConstants.Endpoints.voiceChat)?token=\(token)"
        if let journalType = journalType {
            urlString += "&journal_type=\(journalType)"
        }

        guard let url = URL(string: urlString) else {
            print("[WebSocket] Invalid URL")
            return
        }

        print("[WebSocket] Connecting to \(url)")
        webSocket = session.webSocketTask(with: url)
        webSocket?.resume()
        receiveMessage()
    }

    func disconnect() {
        print("[WebSocket] Disconnecting")
        webSocket?.cancel(with: .normalClosure, reason: nil)
        webSocket = nil
        isConnected = false
    }

    func sendAudio(_ data: Data) {
        guard isConnected else {
            print("[WebSocket] Cannot send audio - not connected")
            return
        }
        print("[WebSocket] Sending \(data.count) bytes of audio")
        webSocket?.send(.data(data)) { error in
            if let error = error {
                print("[WebSocket] Failed to send audio: \(error)")
            }
        }
    }

    func sendMessage(_ message: VoiceSendMessage) {
        guard isConnected else { return }
        do {
            let data = try JSONEncoder().encode(message)
            webSocket?.send(.string(String(data: data, encoding: .utf8)!)) { error in
                if let error = error {
                    print("[WebSocket] Failed to send message: \(error)")
                }
            }
        } catch {
            print("[WebSocket] Failed to encode message: \(error)")
        }
    }

    func sendInterrupt() {
        sendMessage(VoiceSendMessage(type: "interrupt"))
    }

    func sendPing() {
        sendMessage(VoiceSendMessage(type: "ping"))
    }

    private func receiveMessage() {
        webSocket?.receive { [weak self] result in
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self?.handleTextMessage(text)
                case .data(let data):
                    self?.delegate?.webSocketDidReceiveAudio(data)
                @unknown default:
                    break
                }
                self?.receiveMessage()

            case .failure(let error):
                print("[WebSocket] Receive error: \(error)")
                self?.isConnected = false
                self?.delegate?.webSocketDidDisconnect(error: error)
            }
        }
    }

    private func handleTextMessage(_ text: String) {
        guard let data = text.data(using: .utf8) else { return }

        do {
            let message = try JSONDecoder().decode(VoiceControlMessage.self, from: data)
            print("[WebSocket] Received: \(message.type)")

            if message.type == .ready && !isConnected {
                isConnected = true
                delegate?.webSocketDidConnect()
            }

            delegate?.webSocketDidReceiveMessage(message)
        } catch {
            print("[WebSocket] Failed to decode message: \(error), text: \(text)")
        }
    }
}

extension WebSocketManager: URLSessionWebSocketDelegate {
    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
        print("[WebSocket] Connected")
        isConnected = true
    }

    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
        print("[WebSocket] Closed with code: \(closeCode)")
        isConnected = false
        delegate?.webSocketDidDisconnect(error: nil)
    }
}
