'use client';

import Image from 'next/image';
import { cn } from '@/lib/utils';
import type { VoiceChatState } from '@/hooks/useVoiceChat';

interface JournalBuddyAvatarProps {
  state: VoiceChatState;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function JournalBuddyAvatar({ state, className, size = 'lg' }: JournalBuddyAvatarProps) {
  const sizeClasses = {
    sm: 'w-24 h-24',
    md: 'w-40 h-40',
    lg: 'w-64 h-64',
  };

  const stateColors = {
    disconnected: 'bg-gray-100',
    connecting: 'bg-blue-50',
    idle: 'bg-gradient-to-br from-blue-50 to-purple-50',
    listening: 'bg-gradient-to-br from-green-50 to-emerald-50',
    thinking: 'bg-gradient-to-br from-yellow-50 to-amber-50',
    speaking: 'bg-gradient-to-br from-purple-50 to-pink-50',
  };

  const stateAnimations = {
    disconnected: '',
    connecting: 'animate-pulse',
    idle: 'animate-float',
    listening: 'animate-listen',
    thinking: 'animate-think',
    speaking: 'animate-speak',
  };

  return (
    <div className={cn('relative flex items-center justify-center', className)}>
      <div
        className={cn(
          'relative rounded-full flex items-center justify-center transition-all duration-500',
          sizeClasses[size],
          stateColors[state]
        )}
      >
        {state === 'listening' && (
          <div className="absolute inset-0 rounded-full">
            <div className="absolute inset-0 rounded-full border-4 border-green-400 animate-ping opacity-30" />
            <div className="absolute inset-2 rounded-full border-2 border-green-300 animate-ping opacity-20 animation-delay-150" />
          </div>
        )}

        {state === 'speaking' && (
          <div className="absolute inset-0 rounded-full">
            <div className="absolute inset-0 rounded-full bg-purple-200 animate-pulse opacity-30" />
            <SoundWaves className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-8" />
          </div>
        )}

        {state === 'thinking' && (
          <div className="absolute -top-2 right-0">
            <ThinkingDots />
          </div>
        )}

        <div className={cn('relative z-10 transition-transform duration-300', stateAnimations[state])}>
          <Image
            src="/journal-buddy-avatar.png"
            alt="JournalBuddy"
            width={size === 'lg' ? 200 : size === 'md' ? 120 : 80}
            height={size === 'lg' ? 200 : size === 'md' ? 120 : 80}
            className="drop-shadow-lg"
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
    <div className="flex gap-1">
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-yellow-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
    </div>
  );
}

function SoundWaves({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-end gap-0.5 h-8', className)}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-1 bg-purple-500 rounded-full animate-sound-wave"
          style={{
            height: '50%',
            animationDelay: `${i * 100}ms`,
          }}
        />
      ))}
    </div>
  );
}
