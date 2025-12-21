import AVFoundation
import Foundation

protocol AudioEngineDelegate: AnyObject {
    func audioEngineDidCaptureAudio(_ data: Data)
}

class AudioEngineManager {
    weak var delegate: AudioEngineDelegate?

    private var audioEngine: AVAudioEngine?
    private var playerNode: AVAudioPlayerNode?
    private var inputNode: AVAudioInputNode?

    private let inputSampleRate: Double = 16000
    private let outputSampleRate: Double = 24000

    private var audioBuffer = Data()
    private let bufferQueue = DispatchQueue(label: "audio.buffer.queue")

    private var isRecording = false
    private var isPlaying = false

    init() {
        setupAudioSession()
    }

    private func setupAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
            print("[Audio] Session configured")
        } catch {
            print("[Audio] Failed to configure session: \(error)")
        }
    }

    func startRecording() {
        guard !isRecording else { return }

        audioEngine = AVAudioEngine()
        guard let audioEngine = audioEngine else { return }

        inputNode = audioEngine.inputNode
        guard let inputNode = inputNode else { return }

        let inputFormat = inputNode.outputFormat(forBus: 0)
        print("[Audio] Input format: \(inputFormat.sampleRate)Hz, \(inputFormat.channelCount) channels, \(inputFormat.commonFormat.rawValue)")

        let bufferSize: AVAudioFrameCount = 4096

        inputNode.installTap(onBus: 0, bufferSize: bufferSize, format: inputFormat) { [weak self] buffer, _ in
            self?.processInputBuffer(buffer)
        }

        do {
            try audioEngine.start()
            isRecording = true
            print("[Audio] Recording started with tap installed")
        } catch {
            print("[Audio] Failed to start engine: \(error)")
        }
    }

    private func processInputBuffer(_ buffer: AVAudioPCMBuffer) {
        guard buffer.frameLength > 0 else {
            print("[Audio] Empty buffer received")
            return
        }

        guard let floatData = buffer.floatChannelData else {
            print("[Audio] No float channel data")
            return
        }

        let frameCount = Int(buffer.frameLength)
        var int16Data = [Int16](repeating: 0, count: frameCount)

        for i in 0..<frameCount {
            let sample = floatData[0][i]
            let clampedSample = max(-1.0, min(1.0, sample))
            int16Data[i] = Int16(clampedSample * Float(Int16.max))
        }

        let data = int16Data.withUnsafeBufferPointer { buffer in
            Data(buffer: buffer)
        }

        print("[Audio] Captured \(data.count) bytes (\(frameCount) frames)")
        delegate?.audioEngineDidCaptureAudio(data)
    }

    func stopRecording() {
        guard isRecording else { return }

        inputNode?.removeTap(onBus: 0)
        audioEngine?.stop()
        audioEngine = nil
        inputNode = nil
        isRecording = false
        print("[Audio] Recording stopped")
    }

    func playAudio(_ data: Data) {
        bufferQueue.async { [weak self] in
            self?.audioBuffer.append(data)
            self?.processAudioBuffer()
        }
    }

    private func processAudioBuffer() {
        guard audioBuffer.count >= 4800 else { return }

        let chunkSize = 4800
        let chunk = audioBuffer.prefix(chunkSize)
        audioBuffer.removeFirst(min(chunkSize, audioBuffer.count))

        DispatchQueue.main.async { [weak self] in
            self?.playChunk(Data(chunk))
        }
    }

    private func playChunk(_ data: Data) {
        if playerNode == nil {
            setupPlayer()
        }

        guard let playerNode = playerNode, let audioEngine = audioEngine else { return }

        let frameCount = UInt32(data.count / 2)
        guard let format = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: outputSampleRate, channels: 1, interleaved: true),
              let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
            return
        }

        buffer.frameLength = frameCount

        data.withUnsafeBytes { rawBuffer in
            if let baseAddress = rawBuffer.baseAddress {
                memcpy(buffer.int16ChannelData![0], baseAddress, data.count)
            }
        }

        if let floatFormat = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: outputSampleRate, channels: 1, interleaved: true),
           let floatBuffer = AVAudioPCMBuffer(pcmFormat: floatFormat, frameCapacity: frameCount),
           let converter = AVAudioConverter(from: format, to: floatFormat) {

            floatBuffer.frameLength = frameCount

            var error: NSError?
            converter.convert(to: floatBuffer, error: &error) { _, outStatus in
                outStatus.pointee = .haveData
                return buffer
            }

            if !isPlaying {
                do {
                    try audioEngine.start()
                    playerNode.play()
                    isPlaying = true
                } catch {
                    print("[Audio] Failed to start playback: \(error)")
                    return
                }
            }

            playerNode.scheduleBuffer(floatBuffer, completionHandler: nil)
        }
    }

    private func setupPlayer() {
        audioEngine = AVAudioEngine()
        playerNode = AVAudioPlayerNode()

        guard let audioEngine = audioEngine, let playerNode = playerNode else { return }

        audioEngine.attach(playerNode)

        let format = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: outputSampleRate, channels: 1, interleaved: true)!
        audioEngine.connect(playerNode, to: audioEngine.mainMixerNode, format: format)

        do {
            try audioEngine.start()
            print("[Audio] Player setup complete")
        } catch {
            print("[Audio] Failed to setup player: \(error)")
        }
    }

    func stopPlayback() {
        playerNode?.stop()
        audioEngine?.stop()
        isPlaying = false
        bufferQueue.async { [weak self] in
            self?.audioBuffer.removeAll()
        }
        print("[Audio] Playback stopped")
    }

    func reset() {
        stopRecording()
        stopPlayback()
        playerNode = nil
        audioEngine = nil
    }
}
