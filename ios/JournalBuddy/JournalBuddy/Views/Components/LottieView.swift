import SwiftUI
import Lottie

struct LottieView: UIViewRepresentable {
    let animationName: String
    var loopMode: LottieLoopMode = .loop
    var contentMode: UIView.ContentMode = .scaleAspectFit
    var animationSpeed: CGFloat = 1.0
    var play: Bool = true

    func makeUIView(context: Context) -> LottieAnimationView {
        let animationView = LottieAnimationView(name: animationName)
        animationView.contentMode = contentMode
        animationView.loopMode = loopMode
        animationView.animationSpeed = animationSpeed
        animationView.backgroundBehavior = .pauseAndRestore

        if play {
            animationView.play()
        }

        return animationView
    }

    func updateUIView(_ uiView: LottieAnimationView, context: Context) {
        uiView.loopMode = loopMode
        uiView.animationSpeed = animationSpeed

        if play && !uiView.isAnimationPlaying {
            uiView.play()
        } else if !play && uiView.isAnimationPlaying {
            uiView.pause()
        }
    }
}

struct LottieAnimationSwitcher: UIViewRepresentable {
    let animationName: String
    var loopMode: LottieLoopMode = .loop
    var animationSpeed: CGFloat = 1.0

    func makeUIView(context: Context) -> LottieAnimationView {
        let animationView = LottieAnimationView(name: animationName)
        animationView.contentMode = .scaleAspectFit
        animationView.loopMode = loopMode
        animationView.animationSpeed = animationSpeed
        animationView.backgroundBehavior = .pauseAndRestore
        animationView.play()
        return animationView
    }

    func updateUIView(_ uiView: LottieAnimationView, context: Context) {
        if uiView.animation?.name != animationName {
            uiView.animation = LottieAnimation.named(animationName)
            uiView.loopMode = loopMode
            uiView.animationSpeed = animationSpeed
            uiView.play()
        }
    }
}

#Preview {
    VStack {
        LottieView(animationName: "avatar_idle")
            .frame(width: 200, height: 200)
    }
}
