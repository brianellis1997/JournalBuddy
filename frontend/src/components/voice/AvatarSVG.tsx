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
    mouthPath: 'M 42,72 Q 50,78 58,72',
    eyeScale: 1,
    leftArmRotation: 0,
  },
  happy: {
    eyebrowY: -1,
    eyebrowRotation: 0,
    mouthPath: 'M 40,70 Q 50,82 60,70',
    eyeScale: 1.05,
    leftArmRotation: -20,
  },
  warm: {
    eyebrowY: -1,
    eyebrowRotation: 0,
    mouthPath: 'M 42,71 Q 50,80 58,71',
    eyeScale: 1,
    leftArmRotation: 0,
  },
  concerned: {
    eyebrowY: 1,
    eyebrowRotation: 8,
    mouthPath: 'M 42,76 Q 50,72 58,76',
    eyeScale: 0.95,
    leftArmRotation: 0,
  },
  curious: {
    eyebrowY: -2,
    eyebrowRotation: -5,
    mouthPath: 'M 46,73 Q 50,76 54,73',
    eyeScale: 1.1,
    leftArmRotation: 0,
  },
  encouraging: {
    eyebrowY: -1,
    eyebrowRotation: 0,
    mouthPath: 'M 40,68 Q 50,82 60,68',
    eyeScale: 1.08,
    leftArmRotation: -30,
  },
  celebrating: {
    eyebrowY: -2,
    eyebrowRotation: 0,
    mouthPath: 'M 38,66 Q 50,85 62,66',
    eyeScale: 1.15,
    leftArmRotation: -45,
  },
};

export function AvatarSVG({ emotion, isListening, isSpeaking, className, size = 200 }: AvatarSVGProps) {
  const style = emotionStyles[emotion] || emotionStyles.neutral;
  const isThumbsUp = style.leftArmRotation < -15;

  return (
    <svg
      viewBox="0 0 100 120"
      width={size}
      height={size * 1.2}
      className={cn('transition-all duration-300', className)}
    >
      <defs>
        <linearGradient id="bookGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#7EC8E3" />
          <stop offset="100%" stopColor="#5BB5D4" />
        </linearGradient>
        <linearGradient id="pageGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFFFF5" />
          <stop offset="100%" stopColor="#F5F5DC" />
        </linearGradient>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="2" dy="2" stdDeviation="2" floodOpacity="0.2"/>
        </filter>
      </defs>

      {/* Shadow on ground */}
      <ellipse cx="50" cy="115" rx="25" ry="5" fill="#E5E5E5" />

      {/* Left arm (behind book) */}
      <g
        className="transition-transform duration-300"
        style={{
          transform: `rotate(${style.leftArmRotation}deg)`,
          transformOrigin: '20px 65px',
        }}
      >
        {/* Arm */}
        <path
          d="M 20,65 Q 5,55 0,45"
          fill="none"
          stroke="#2C2C2C"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Hand/glove */}
        <ellipse
          cx={isThumbsUp ? 2 : 0}
          cy={isThumbsUp ? 42 : 45}
          rx="6"
          ry="5"
          fill="#FF8C42"
          className="transition-all duration-300"
        />
        {/* Thumb (only visible when thumbs up) */}
        {isThumbsUp && (
          <ellipse cx="-2" cy="36" rx="3" ry="5" fill="#FF8C42" />
        )}
      </g>

      {/* Spiral binding */}
      <g>
        {[25, 35, 45, 55, 65, 75].map((y, i) => (
          <ellipse
            key={i}
            cx="22"
            cy={y}
            rx="4"
            ry="3"
            fill="none"
            stroke="#A0A0A0"
            strokeWidth="1.5"
          />
        ))}
      </g>

      {/* Pages (top of book) */}
      <rect x="28" y="18" width="47" height="6" rx="1" fill="url(#pageGradient)" />
      <line x1="30" y1="20" x2="73" y2="20" stroke="#DDD" strokeWidth="0.5" />
      <line x1="30" y1="22" x2="73" y2="22" stroke="#DDD" strokeWidth="0.5" />

      {/* Red bookmark */}
      <path d="M 60,15 L 60,30 L 63,27 L 66,30 L 66,15 Z" fill="#E63946" />

      {/* Main book body */}
      <rect
        x="25"
        y="24"
        width="50"
        height="60"
        rx="3"
        fill="url(#bookGradient)"
        filter="url(#shadow)"
        className={cn(
          'transition-transform duration-300',
          isListening && 'animate-breathe'
        )}
      />

      {/* Book spine highlight */}
      <rect x="25" y="24" width="4" height="60" rx="2" fill="#6BBCD6" opacity="0.5" />

      {/* Right arm */}
      <g>
        {/* Arm */}
        <path
          d="M 75,65 Q 88,60 92,55"
          fill="none"
          stroke="#2C2C2C"
          strokeWidth="3"
          strokeLinecap="round"
        />
        {/* Hand/glove */}
        <ellipse cx="94" cy="53" rx="6" ry="5" fill="#FF8C42" />
      </g>

      {/* Legs */}
      <line x1="40" y1="84" x2="40" y2="100" stroke="#2C2C2C" strokeWidth="3" strokeLinecap="round" />
      <line x1="60" y1="84" x2="60" y2="100" stroke="#2C2C2C" strokeWidth="3" strokeLinecap="round" />

      {/* Shoes */}
      <ellipse cx="40" cy="103" rx="7" ry="5" fill="#FF8C42" />
      <ellipse cx="60" cy="103" rx="7" ry="5" fill="#FF8C42" />

      {/* Eyes */}
      <g className={cn('transition-transform duration-300', isListening && 'animate-blink')}>
        {/* Left eye */}
        <ellipse
          cx="38"
          cy="50"
          rx={7 * style.eyeScale}
          ry={8 * style.eyeScale}
          fill="white"
        />
        <circle cx="38" cy="51" r={4 * style.eyeScale} fill="#2C2C2C" />
        <circle cx="40" cy="49" r={1.5} fill="white" />

        {/* Right eye */}
        <ellipse
          cx="62"
          cy="50"
          rx={7 * style.eyeScale}
          ry={8 * style.eyeScale}
          fill="white"
        />
        <circle cx="62" cy="51" r={4 * style.eyeScale} fill="#2C2C2C" />
        <circle cx="64" cy="49" r={1.5} fill="white" />
      </g>

      {/* Eyebrows */}
      <g
        className="transition-transform duration-300"
        style={{
          transform: `translateY(${style.eyebrowY}px)`,
        }}
      >
        <path
          d={`M 32,${40 + style.eyebrowRotation * 0.3} Q 38,${38} 44,${40 - style.eyebrowRotation * 0.3}`}
          fill="none"
          stroke="#5D4E37"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <path
          d={`M 56,${40 - style.eyebrowRotation * 0.3} Q 62,${38} 68,${40 + style.eyebrowRotation * 0.3}`}
          fill="none"
          stroke="#5D4E37"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </g>

      {/* Cheek blushes */}
      <ellipse cx="30" cy="60" rx="5" ry="3" fill="#FFB6B6" opacity="0.6" />
      <ellipse cx="70" cy="60" rx="5" ry="3" fill="#FFB6B6" opacity="0.6" />

      {/* Mouth */}
      <path
        d={style.mouthPath}
        fill={isSpeaking ? "#E63946" : "none"}
        stroke="#2C2C2C"
        strokeWidth="2"
        strokeLinecap="round"
        className={cn(
          'transition-all duration-150',
          isSpeaking && 'animate-mouth-speak'
        )}
      />

      {/* Tongue (visible when mouth is open/speaking or celebrating) */}
      {(isSpeaking || emotion === 'celebrating' || emotion === 'happy') && (
        <ellipse cx="50" cy="76" rx="4" ry="3" fill="#FF6B6B" opacity="0.8" />
      )}
    </svg>
  );
}
