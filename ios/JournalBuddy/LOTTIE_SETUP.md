# Lottie Avatar Animations Setup

This guide explains how to set up Lottie animations for the JournalBuddy avatar.

## 1. Add Lottie Package

In Xcode:
1. File → Add Package Dependencies...
2. Enter: `https://github.com/airbnb/lottie-ios`
3. Select version 4.x or later
4. Click "Add Package"

## 2. Required Animation Files

Create or download Lottie JSON animations for each state and emotion. Place them in the project's Assets folder or a "Animations" group.

### Required Animations

| File Name | Description |
|-----------|-------------|
| `avatar_idle.json` | Default idle/breathing animation |
| `avatar_connecting.json` | Loading/connecting state |
| `avatar_listening.json` | Actively listening (ears perked) |
| `avatar_thinking.json` | Processing/thinking animation |
| `avatar_speaking.json` | Speaking/talking animation |
| `avatar_neutral.json` | Neutral emotion (can be same as idle) |
| `avatar_happy.json` | Happy/smiling expression |
| `avatar_warm.json` | Warm/caring expression |
| `avatar_concerned.json` | Concerned/worried expression |
| `avatar_curious.json` | Curious/interested expression |
| `avatar_encouraging.json` | Encouraging/supportive expression |
| `avatar_celebrating.json` | Celebratory/excited expression |

## 3. Animation Guidelines

### Design Specifications
- **Size**: 400x400 pixels recommended
- **Frame Rate**: 30 fps
- **Duration**: 2-4 seconds for loops
- **Style**: Consistent character design across all animations

### Emotion Animations
Emotion animations should:
- Loop seamlessly
- Have subtle, expressive movements
- Transition smoothly (consider using fade between states)

### State Animations
- **Idle**: Gentle breathing, subtle movement
- **Listening**: Alert posture, maybe subtle nods
- **Thinking**: Eyes moving, processing visual
- **Speaking**: Mouth movement, expressive gestures

## 4. Free Resources

You can find avatar animations on:
- [LottieFiles](https://lottiefiles.com/) - Search for "avatar" or "character"
- [IconScout](https://iconscout.com/lottie-animations)
- [Lordicon](https://lordicon.com/)

Or create custom animations with:
- Adobe After Effects + Bodymovin plugin
- [LottieCreator](https://app.lottiefiles.com/creator)
- [Haiku Animator](https://www.haikuanimator.com/)

## 5. Adding Animations to Project

1. Download or create your Lottie JSON files
2. Drag them into your Xcode project
3. Make sure "Copy items if needed" is checked
4. Add to the JournalBuddy target

## 6. Enable in Settings

Once animations are added:
1. Open the app
2. Go to Profile → Buddy's Voice
3. Enable "Animated Avatar" toggle

## 7. Fallback Behavior

If Lottie animation files are not found, the app will automatically fall back to the static image-based avatar with SwiftUI animations.

## 8. Testing

Use the Preview in `LottieAvatarView.swift` to test animations:
```swift
#Preview {
    LottieAvatarView(state: .speaking, emotion: .happy, isAudioPlaying: true)
}
```

## Troubleshooting

### Animation Not Playing
- Verify the JSON file is correctly named
- Check that the file is included in the target
- Ensure Lottie package is properly installed

### Performance Issues
- Optimize animations to reduce complexity
- Use simpler shapes and fewer keyframes
- Consider caching animations
