'use client';

import { cn } from '@/lib/utils';
import type { AvatarEmotion } from '@/hooks/useVoiceChat';

interface AvatarSVGProps {
  emotion: AvatarEmotion;
  isListening?: boolean;
  isSpeaking?: boolean;
  className?: string;
  size?: number;
}

const emotionStyles = {
  neutral: {
    eyebrowY: 0,
    eyebrowRotation: 0,
    mouthPath: 'M 35,65 Q 50,65 65,65',
    eyeScale: 1,
  },
  happy: {
    eyebrowY: -2,
    eyebrowRotation: 0,
    mouthPath: 'M 35,62 Q 50,72 65,62',
    eyeScale: 1.05,
  },
  warm: {
    eyebrowY: -1,
    eyebrowRotation: 0,
    mouthPath: 'M 35,63 Q 50,70 65,63',
    eyeScale: 1,
  },
  concerned: {
    eyebrowY: 0,
    eyebrowRotation: 5,
    mouthPath: 'M 35,68 Q 50,63 65,68',
    eyeScale: 0.95,
  },
  curious: {
    eyebrowY: -3,
    eyebrowRotation: -3,
    mouthPath: 'M 38,65 Q 50,66 62,65',
    eyeScale: 1.1,
  },
  encouraging: {
    eyebrowY: -2,
    eyebrowRotation: 0,
    mouthPath: 'M 35,60 Q 50,73 65,60',
    eyeScale: 1.08,
  },
  celebrating: {
    eyebrowY: -4,
    eyebrowRotation: 0,
    mouthPath: 'M 32,58 Q 50,78 68,58',
    eyeScale: 1.15,
  },
};

export function AvatarSVG({ emotion, isListening, isSpeaking, className, size = 200 }: AvatarSVGProps) {
  const style = emotionStyles[emotion] || emotionStyles.neutral;

  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={cn('transition-all duration-300', className)}
    >
      <defs>
        <linearGradient id="faceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFE0BD" />
          <stop offset="100%" stopColor="#FFCBA4" />
        </linearGradient>
        <linearGradient id="cheekGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFB6B6" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#FFB6B6" stopOpacity="0" />
        </linearGradient>
      </defs>

      <circle
        cx="50"
        cy="50"
        r="45"
        fill="url(#faceGradient)"
        className={cn(
          'transition-transform duration-300',
          isListening && 'animate-breathe',
          isSpeaking && 'animate-speak'
        )}
      />

      <ellipse cx="30" cy="62" rx="8" ry="5" fill="url(#cheekGradient)" />
      <ellipse cx="70" cy="62" rx="8" ry="5" fill="url(#cheekGradient)" />

      <g
        className="transition-transform duration-300"
        style={{
          transform: `translateY(${style.eyebrowY}px) rotate(${style.eyebrowRotation}deg)`,
          transformOrigin: '35px 35px',
        }}
      >
        <path
          d="M 28,35 Q 35,32 42,35"
          fill="none"
          stroke="#5D4E37"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </g>

      <g
        className="transition-transform duration-300"
        style={{
          transform: `translateY(${style.eyebrowY}px) rotate(${-style.eyebrowRotation}deg)`,
          transformOrigin: '65px 35px',
        }}
      >
        <path
          d="M 58,35 Q 65,32 72,35"
          fill="none"
          stroke="#5D4E37"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </g>

      <g className={cn('transition-transform duration-300', isListening && 'animate-blink')}>
        <ellipse
          cx="35"
          cy="45"
          rx={5 * style.eyeScale}
          ry={6 * style.eyeScale}
          fill="white"
        />
        <circle cx="35" cy="45" r={3 * style.eyeScale} fill="#4A3728" />
        <circle cx="36" cy="44" r={1} fill="white" />
      </g>

      <g className={cn('transition-transform duration-300', isListening && 'animate-blink')}>
        <ellipse
          cx="65"
          cy="45"
          rx={5 * style.eyeScale}
          ry={6 * style.eyeScale}
          fill="white"
        />
        <circle cx="65" cy="45" r={3 * style.eyeScale} fill="#4A3728" />
        <circle cx="66" cy="44" r={1} fill="white" />
      </g>

      <path
        d={style.mouthPath}
        fill="none"
        stroke="#D4726A"
        strokeWidth="3"
        strokeLinecap="round"
        className={cn(
          'transition-all duration-300',
          isSpeaking && 'animate-mouth-speak'
        )}
      />

      {(emotion === 'happy' || emotion === 'celebrating' || emotion === 'encouraging') && (
        <>
          <circle cx="25" cy="48" r="2" fill="#FFB6B6" opacity="0.6" />
          <circle cx="75" cy="48" r="2" fill="#FFB6B6" opacity="0.6" />
        </>
      )}
    </svg>
  );
}
