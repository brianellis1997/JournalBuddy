'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';
import type { VoiceChatState, AvatarEmotion } from '@/hooks/useVoiceChat';

interface JournalBuddyAvatarProps {
  state: VoiceChatState;
  emotion?: AvatarEmotion;
  isAudioPlaying?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const emotionToImage: Record<AvatarEmotion, string> = {
  neutral: '/avatars/neutral.png',
  happy: '/avatars/Happy.png',
  warm: '/avatars/Encouraging.png',
  concerned: '/avatars/Concerned.png',
  curious: '/avatars/Thinking.png',
  encouraging: '/avatars/Encouraging.png',
  celebrating: '/avatars/Happy.png',
};

const speakingImages = ['/avatars/Speaking_1.png', '/avatars/Speaking_2.png'];

export function JournalBuddyAvatar({ state, emotion = 'neutral', isAudioPlaying = false, className, size = 'lg' }: JournalBuddyAvatarProps) {
  const [speakingFrame, setSpeakingFrame] = useState(0);

  useEffect(() => {
    if (!isAudioPlaying) {
      setSpeakingFrame(0);
      return;
    }

    const interval = setInterval(() => {
      setSpeakingFrame(prev => (prev + 1) % 2);
    }, 150);

    return () => clearInterval(interval);
  }, [isAudioPlaying]);

  const sizeConfig = {
    sm: { container: 'w-16 h-16', image: 64 },
    md: { container: 'w-32 h-32', image: 128 },
    lg: { container: 'w-48 h-48', image: 192 },
  };

  const stateColors = {
    disconnected: 'bg-gray-100',
    connecting: 'bg-blue-50',
    idle: 'bg-gradient-to-br from-blue-50 to-purple-50',
    listening: 'bg-gradient-to-br from-green-50 to-emerald-50',
    thinking: 'bg-gradient-to-br from-yellow-50 to-amber-50',
    speaking: 'bg-gradient-to-br from-purple-50 to-pink-50',
  };

  const imageSrc = isAudioPlaying
    ? speakingImages[speakingFrame]
    : emotionToImage[emotion] || emotionToImage.neutral;

  return (
    <div className={cn('relative flex items-center justify-center', className)}>
      <div
        className={cn(
          'relative rounded-full flex items-center justify-center transition-all duration-500 overflow-hidden',
          sizeConfig[size].container,
          stateColors[state]
        )}
      >
        {state === 'listening' && (
          <div className="absolute inset-0 rounded-full">
            <div className="absolute inset-0 rounded-full border-4 border-green-400 animate-ping opacity-30" />
            <div className="absolute inset-2 rounded-full border-2 border-green-300 animate-ping opacity-20" style={{ animationDelay: '150ms' }} />
          </div>
        )}

        {state === 'speaking' && (
          <div className="absolute inset-0 rounded-full">
            <div className="absolute inset-0 rounded-full bg-purple-200 animate-pulse opacity-30" />
          </div>
        )}

        {state === 'thinking' && (
          <div className="absolute -top-1 -right-1 z-20">
            <ThinkingDots />
          </div>
        )}

        <div className={cn(
          'relative z-10 transition-all duration-300',
          state === 'connecting' && 'animate-pulse',
          state === 'idle' && 'animate-float',
        )}>
          <Image
            src={imageSrc}
            alt="JournalBuddy"
            width={sizeConfig[size].image}
            height={sizeConfig[size].image}
            className="object-contain drop-shadow-lg"
            priority
          />
        </div>
      </div>

      {size !== 'sm' && <StateIndicator state={state} />}
    </div>
  );
}

function StateIndicator({ state }: { state: VoiceChatState }) {
  const stateLabels = {
    disconnected: 'Offline',
    connecting: 'Connecting...',
    idle: 'Ready to chat',
    listening: 'Listening...',
    thinking: 'Thinking...',
    speaking: 'Speaking...',
  };

  const stateColorClasses = {
    disconnected: 'bg-gray-400',
    connecting: 'bg-blue-400 animate-pulse',
    idle: 'bg-green-400',
    listening: 'bg-green-500 animate-pulse',
    thinking: 'bg-yellow-500 animate-pulse',
    speaking: 'bg-purple-500 animate-pulse',
  };

  return (
    <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-2">
      <div className={cn('w-2 h-2 rounded-full', stateColorClasses[state])} />
      <span className="text-sm text-gray-600 whitespace-nowrap">{stateLabels[state]}</span>
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex gap-1 bg-white/80 rounded-full px-2 py-1 shadow-sm">
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  );
}
