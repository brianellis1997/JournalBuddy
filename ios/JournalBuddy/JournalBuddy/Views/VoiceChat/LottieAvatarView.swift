import SwiftUI
import Lottie

struct LottieAvatarView: View {
    let state: VoiceChatState
    let emotion: AvatarEmotion
    var isAudioPlaying: Bool = false

    @State private var glowOpacity: Double = 0.3
    @State private var pulseScale: CGFloat = 1.0

    var body: some View {
        ZStack {
            backgroundGlow

            Circle()
                .fill(stateBackgroundColor)
                .frame(width: 180, height: 180)

            animationView
                .frame(width: 160, height: 160)
                .clipShape(Circle())
                .scaleEffect(pulseScale)
                .shadow(color: shadowColor.opacity(0.4), radius: 15)

            if state == .thinking {
                thinkingIndicator
            }
        }
        .onAppear {
            startBreathingAnimation()
        }
        .onChange(of: state) { _, newState in
            updateAnimation(for: newState)
        }
    }

    private var animationView: some View {
        LottieAnimationSwitcher(
            animationName: currentAnimationName,
            loopMode: .loop,
            animationSpeed: animationSpeed
        )
    }

    private var currentAnimationName: String {
        if isAudioPlaying {
            return "avatar_speaking"
        }

        switch state {
        case .disconnected:
            return "avatar_idle"
        case .connecting:
            return "avatar_connecting"
        case .idle:
            return emotionAnimation
        case .listening:
            return "avatar_listening"
        case .thinking:
            return "avatar_thinking"
        case .speaking:
            return "avatar_speaking"
        }
    }

    private var emotionAnimation: String {
        switch emotion {
        case .neutral:
            return "avatar_neutral"
        case .happy:
            return "avatar_happy"
        case .warm:
            return "avatar_warm"
        case .concerned:
            return "avatar_concerned"
        case .curious:
            return "avatar_curious"
        case .encouraging:
            return "avatar_encouraging"
        case .celebrating:
            return "avatar_celebrating"
        }
    }

    private var animationSpeed: CGFloat {
        switch state {
        case .speaking:
            return isAudioPlaying ? 1.5 : 1.0
        case .thinking:
            return 0.8
        case .connecting:
            return 1.2
        default:
            return 1.0
        }
    }

    private var backgroundGlow: some View {
        Circle()
            .fill(glowColor.opacity(glowOpacity))
            .frame(width: 220, height: 220)
            .blur(radius: 30)
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

    @State private var thinkingDotIndex: Int = 0
    let thinkingTimer = Timer.publish(every: 0.4, on: .main, in: .common).autoconnect()

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
        .onReceive(thinkingTimer) { _ in
            if state == .thinking {
                thinkingDotIndex = (thinkingDotIndex + 1) % 3
            }
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

#Preview {
    VStack(spacing: 40) {
        LottieAvatarView(state: .idle, emotion: .neutral, isAudioPlaying: false)
        LottieAvatarView(state: .speaking, emotion: .happy, isAudioPlaying: true)
    }
    .padding()
    .background(Color.black.opacity(0.9))
}
