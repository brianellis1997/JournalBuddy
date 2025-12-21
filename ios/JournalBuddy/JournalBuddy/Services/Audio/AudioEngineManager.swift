import AVFoundation
import Foundation

protocol AudioEngineDelegate: AnyObject {
    func audioEngineDidCaptureAudio(_ data: Data)
    func audioEngineDidStartPlaying()
    func audioEngineDidStopPlaying()
}

class AudioEngineManager {
    weak var delegate: AudioEngineDelegate?

    private var recordingEngine: AVAudioEngine?
    private var playbackEngine: AVAudioEngine?
    private var playerNode: AVAudioPlayerNode?

    private let targetSampleRate: Double = 48000
    private let outputSampleRate: Double = 24000

    private var audioBuffer = Data()
    private let bufferQueue = DispatchQueue(label: "audio.buffer.queue")

    private var isRecording = false
    private(set) var isPlaying = false
    private var shouldCaptureAudio = false
    private var scheduledBufferCount = 0
    private var completedBufferCount = 0
    private let bufferLock = NSLock()

    init() {
        setupAudioSession()
    }

    private func setupAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setPreferredSampleRate(48000)
            try session.setActive(true)
            print("[Audio] Session configured, sample rate: \(session.sampleRate)")
        } catch {
            print("[Audio] Failed to configure session: \(error)")
        }
    }

    func startRecording() {
        if isRecording {
            print("[Audio] Already recording, forcing reset first")
            stopRecording()
        }

        stopPlayback()

        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .voiceChat, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)
            print("[Audio] Audio session reactivated for recording")
        } catch {
            print("[Audio] Failed to configure audio session: \(error)")
            return
        }

        recordingEngine = AVAudioEngine()
        guard let engine = recordingEngine else {
            print("[Audio] Failed to create recording engine")
            return
        }

        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)
        let deviceSampleRate = inputFormat.sampleRate
        print("[Audio] Input format: \(deviceSampleRate)Hz, \(inputFormat.channelCount) channels")

        guard inputFormat.channelCount > 0 else {
            print("[Audio] No audio input channels available")
            recordingEngine = nil
            return
        }

        let bufferSize: AVAudioFrameCount = 4096

        inputNode.installTap(onBus: 0, bufferSize: bufferSize, format: inputFormat) { [weak self] buffer, _ in
            self?.processInputBuffer(buffer, inputSampleRate: deviceSampleRate)
        }

        do {
            try engine.start()
            isRecording = true
            shouldCaptureAudio = true
            print("[Audio] Recording started successfully")
        } catch {
            print("[Audio] Failed to start recording engine: \(error)")
            inputNode.removeTap(onBus: 0)
            recordingEngine = nil
        }
    }

    private func processInputBuffer(_ buffer: AVAudioPCMBuffer, inputSampleRate: Double) {
        guard shouldCaptureAudio else { return }
        guard buffer.frameLength > 0 else { return }
        guard let floatData = buffer.floatChannelData else { return }

        let inputFrameCount = Int(buffer.frameLength)

        var samples: [Float]
        if abs(inputSampleRate - targetSampleRate) > 100 {
            let ratio = targetSampleRate / inputSampleRate
            let outputFrameCount = Int(Double(inputFrameCount) * ratio)
            samples = [Float](repeating: 0, count: outputFrameCount)

            for i in 0..<outputFrameCount {
                let srcIndex = Double(i) / ratio
                let srcIndexInt = Int(srcIndex)
                let frac = Float(srcIndex - Double(srcIndexInt))

                if srcIndexInt + 1 < inputFrameCount {
                    samples[i] = floatData[0][srcIndexInt] * (1 - frac) + floatData[0][srcIndexInt + 1] * frac
                } else if srcIndexInt < inputFrameCount {
                    samples[i] = floatData[0][srcIndexInt]
                }
            }
        } else {
            samples = Array(UnsafeBufferPointer(start: floatData[0], count: inputFrameCount))
        }

        var int16Data = [Int16](repeating: 0, count: samples.count)
        for i in 0..<samples.count {
            let clampedSample = max(-1.0, min(1.0, samples[i]))
            int16Data[i] = Int16(clampedSample * Float(Int16.max))
        }

        let data = int16Data.withUnsafeBufferPointer { buffer in
            Data(buffer: buffer)
        }

        delegate?.audioEngineDidCaptureAudio(data)
    }

    func stopRecording() {
        shouldCaptureAudio = false

        guard isRecording else {
            print("[Audio] Not recording, nothing to stop")
            return
        }

        recordingEngine?.inputNode.removeTap(onBus: 0)
        recordingEngine?.stop()
        recordingEngine = nil
        isRecording = false
        print("[Audio] Recording stopped")
    }

    func playAudio(_ data: Data) {
        shouldCaptureAudio = false

        bufferQueue.async { [weak self] in
            self?.audioBuffer.append(data)
            self?.processAudioBuffer()
        }
    }

    private func processAudioBuffer(flush: Bool = false) {
        let minChunkSize = flush ? 2 : 2400
        guard audioBuffer.count >= minChunkSize else { return }

        let chunkSize = min(2400, audioBuffer.count)
        let chunk = audioBuffer.prefix(chunkSize)
        audioBuffer.removeFirst(chunkSize)

        DispatchQueue.main.async { [weak self] in
            self?.playChunk(Data(chunk))
        }

        if audioBuffer.count >= minChunkSize {
            processAudioBuffer(flush: flush)
        }
    }

    func flushAudioBuffer() {
        bufferQueue.async { [weak self] in
            self?.processAudioBuffer(flush: true)
        }
    }

    private func playChunk(_ data: Data) {
        if playbackEngine == nil || playerNode == nil {
            setupPlayer()
        }

        guard let node = playerNode, let engine = playbackEngine else {
            print("[Audio] Playback engine not available")
            return
        }

        let frameCount = UInt32(data.count / 2)
        guard let format = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: outputSampleRate, channels: 1, interleaved: true),
              let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
            print("[Audio] Failed to create audio format or buffer")
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

            let wasPlaying = isPlaying

            if !engine.isRunning {
                do {
                    try engine.start()
                } catch {
                    print("[Audio] Failed to start playback engine: \(error)")
                    return
                }
            }

            if !isPlaying {
                node.play()
                isPlaying = true
            }

            bufferLock.lock()
            scheduledBufferCount += 1
            bufferLock.unlock()

            if !wasPlaying {
                DispatchQueue.main.async { [weak self] in
                    self?.delegate?.audioEngineDidStartPlaying()
                }
                print("[Audio] Playback started")
            }

            node.scheduleBuffer(floatBuffer) { [weak self] in
                self?.handleBufferCompletion()
            }
        }
    }

    private func handleBufferCompletion() {
        bufferLock.lock()
        completedBufferCount += 1
        let scheduled = scheduledBufferCount
        let completed = completedBufferCount
        bufferLock.unlock()

        if completed >= scheduled {
            bufferQueue.asyncAfter(deadline: .now() + 0.15) { [weak self] in
                guard let self = self else { return }

                self.bufferLock.lock()
                let hasMoreBuffers = self.audioBuffer.count > 0
                let stillPlaying = self.completedBufferCount < self.scheduledBufferCount
                self.bufferLock.unlock()

                if !hasMoreBuffers && !stillPlaying && self.isPlaying {
                    DispatchQueue.main.async {
                        self.notifyPlaybackStopped()
                    }
                }
            }
        }
    }

    private func notifyPlaybackStopped() {
        if isPlaying {
            isPlaying = false
            delegate?.audioEngineDidStopPlaying()
            print("[Audio] Playback finished")
        }
    }

    private func setupPlayer() {
        playbackEngine = AVAudioEngine()
        playerNode = AVAudioPlayerNode()

        guard let engine = playbackEngine, let node = playerNode else { return }

        engine.attach(node)

        let format = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: outputSampleRate, channels: 1, interleaved: true)!
        engine.connect(node, to: engine.mainMixerNode, format: format)

        bufferLock.lock()
        scheduledBufferCount = 0
        completedBufferCount = 0
        bufferLock.unlock()

        do {
            try engine.start()
            print("[Audio] Player setup complete")
        } catch {
            print("[Audio] Failed to setup player: \(error)")
        }
    }

    func stopPlayback() {
        let wasPlaying = isPlaying

        playerNode?.stop()
        playbackEngine?.stop()
        isPlaying = false

        bufferLock.lock()
        scheduledBufferCount = 0
        completedBufferCount = 0
        bufferLock.unlock()

        bufferQueue.async { [weak self] in
            self?.audioBuffer.removeAll()
        }

        playbackEngine = nil
        playerNode = nil

        if wasPlaying {
            delegate?.audioEngineDidStopPlaying()
        }
        print("[Audio] Playback stopped")
    }

    func reset() {
        stopRecording()
        stopPlayback()
    }
}
