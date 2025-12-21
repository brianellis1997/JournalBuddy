import SwiftUI

struct AvatarView: View {
    let state: VoiceChatState
    let emotion: AvatarEmotion

    @State private var pulseScale: CGFloat = 1.0
    @State private var glowOpacity: Double = 0.3
    @State private var thinkingDotIndex: Int = 0
    @State private var speakingImageIndex: Int = 0
    @State private var listenPingScale: CGFloat = 1.0

    let thinkingTimer = Timer.publish(every: 0.4, on: .main, in: .common).autoconnect()
    let speakingTimer = Timer.publish(every: 0.3, on: .main, in: .common).autoconnect()

    var body: some View {
        ZStack {
            backgroundGlow

            avatarContainer
        }
        .onAppear {
            startBreathingAnimation()
        }
        .onChange(of: state) { _, newState in
            updateAnimation(for: newState)
        }
        .onReceive(thinkingTimer) { _ in
            if state == .thinking {
                thinkingDotIndex = (thinkingDotIndex + 1) % 3
            }
        }
        .onReceive(speakingTimer) { _ in
            if state == .speaking {
                speakingImageIndex = speakingImageIndex == 0 ? 1 : 0
            }
        }
    }

    private var backgroundGlow: some View {
        Circle()
            .fill(glowColor.opacity(glowOpacity))
            .frame(width: 220, height: 220)
            .blur(radius: 30)
    }

    private var avatarContainer: some View {
        ZStack {
            if state == .listening {
                listeningPingEffect
            }

            if state == .speaking {
                speakingPulseEffect
            }

            Circle()
                .fill(stateBackgroundColor)
                .frame(width: 180, height: 180)

            avatarImage
                .scaleEffect(pulseScale)

            if state == .thinking {
                thinkingIndicator
            }
        }
    }

    private var listeningPingEffect: some View {
        ZStack {
            Circle()
                .stroke(Color.green.opacity(0.3), lineWidth: 4)
                .frame(width: 190, height: 190)
                .scaleEffect(listenPingScale)
                .opacity(2 - listenPingScale)
                .animation(.easeOut(duration: 1.5).repeatForever(autoreverses: false), value: listenPingScale)

            Circle()
                .stroke(Color.green.opacity(0.2), lineWidth: 2)
                .frame(width: 200, height: 200)
                .scaleEffect(listenPingScale * 0.9)
                .opacity(2 - listenPingScale)
                .animation(.easeOut(duration: 1.5).repeatForever(autoreverses: false).delay(0.15), value: listenPingScale)
        }
        .onAppear {
            listenPingScale = 1.5
        }
    }

    private var speakingPulseEffect: some View {
        Circle()
            .fill(Color.purple.opacity(0.2))
            .frame(width: 200, height: 200)
            .scaleEffect(pulseScale * 1.1)
            .animation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true), value: pulseScale)
    }

    private var stateBackgroundColor: Color {
        switch state {
        case .disconnected:
            return Color(red: 0.95, green: 0.95, blue: 0.95)
        case .connecting:
            return Color(red: 0.9, green: 0.95, blue: 1.0)
        case .idle:
            return Color(red: 0.9, green: 0.92, blue: 0.98)
        case .listening:
            return Color(red: 0.9, green: 0.98, blue: 0.92)
        case .thinking:
            return Color(red: 1.0, green: 0.98, blue: 0.9)
        case .speaking:
            return Color(red: 0.95, green: 0.9, blue: 0.98)
        }
    }

    private var avatarImage: some View {
        Image(currentImageName)
            .resizable()
            .aspectRatio(contentMode: .fit)
            .frame(width: 160, height: 160)
            .clipShape(Circle())
            .shadow(color: shadowColor.opacity(0.4), radius: 15)
    }

    private var currentImageName: String {
        if state == .speaking {
            return speakingImageIndex == 0 ? "BuddySpeaking1" : "BuddySpeaking2"
        }

        switch emotion {
        case .neutral:
            return "BuddyNeutral"
        case .happy:
            return "BuddyHappy"
        case .concerned:
            return "BuddyConcerned"
        case .curious:
            return "BuddyThinking"
        case .encouraging:
            return "BuddyEncouraging"
        }
    }

    private var thinkingIndicator: some View {
        HStack(spacing: 6) {
            ForEach(0..<3, id: \.self) { index in
                Circle()
                    .fill(Color.yellow)
                    .frame(width: 10, height: 10)
                    .offset(y: thinkingDotIndex == index ? -5 : 0)
                    .animation(.easeInOut(duration: 0.15), value: thinkingDotIndex)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.white.opacity(0.9))
        .cornerRadius(20)
        .shadow(color: .black.opacity(0.1), radius: 3)
        .offset(x: 70, y: -70)
    }

    private var glowColor: Color {
        switch state {
        case .disconnected:
            return .gray
        case .connecting:
            return .blue
        case .idle:
            return .journalPrimary
        case .listening:
            return .green
        case .thinking:
            return .yellow
        case .speaking:
            return .purple
        }
    }

    private var shadowColor: Color {
        switch state {
        case .listening: return .green
        case .speaking: return .purple
        case .thinking: return .yellow
        default: return .journalPrimary
        }
    }

    private func startBreathingAnimation() {
        withAnimation(.easeInOut(duration: 3).repeatForever(autoreverses: true)) {
            pulseScale = 1.03
            glowOpacity = 0.4
        }
    }

    private func updateAnimation(for state: VoiceChatState) {
        switch state {
        case .listening:
            withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true)) {
                pulseScale = 1.02
                glowOpacity = 0.5
            }
            withAnimation(.easeOut(duration: 1.5).repeatForever(autoreverses: false)) {
                listenPingScale = 1.5
            }
        case .speaking:
            withAnimation(.easeInOut(duration: 0.3).repeatForever(autoreverses: true)) {
                pulseScale = 1.05
                glowOpacity = 0.55
            }
        case .thinking:
            withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
                pulseScale = 1.01
                glowOpacity = 0.45
            }
        case .connecting:
            withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true)) {
                pulseScale = 1.02
                glowOpacity = 0.3
            }
        default:
            startBreathingAnimation()
        }
    }
}

struct AudioWaveformView: View {
    let isActive: Bool
    let color: Color

    @State private var animationPhases: [CGFloat] = Array(repeating: 0.3, count: 5)

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<5, id: \.self) { index in
                RoundedRectangle(cornerRadius: 2)
                    .fill(color)
                    .frame(width: 4, height: isActive ? animationPhases[index] * 30 : 8)
                    .animation(
                        .easeInOut(duration: 0.3)
                        .repeatForever(autoreverses: true)
                        .delay(Double(index) * 0.1),
                        value: isActive
                    )
            }
        }
        .onAppear {
            if isActive {
                startWaveAnimation()
            }
        }
        .onChange(of: isActive) { _, active in
            if active {
                startWaveAnimation()
            } else {
                resetWaveAnimation()
            }
        }
    }

    private func startWaveAnimation() {
        for i in 0..<5 {
            withAnimation(.easeInOut(duration: Double.random(in: 0.2...0.5)).repeatForever(autoreverses: true).delay(Double(i) * 0.1)) {
                animationPhases[i] = CGFloat.random(in: 0.4...1.0)
            }
        }
    }

    private func resetWaveAnimation() {
        for i in 0..<5 {
            animationPhases[i] = 0.3
        }
    }
}

#Preview {
    VStack(spacing: 40) {
        AvatarView(state: .idle, emotion: .neutral)
        AvatarView(state: .listening, emotion: .curious)
        AvatarView(state: .speaking, emotion: .happy)
    }
    .padding()
    .background(Color.black.opacity(0.9))
}
