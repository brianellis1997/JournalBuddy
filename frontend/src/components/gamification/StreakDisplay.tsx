'use client';

import { Flame } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StreakDisplayProps {
  currentStreak: number;
  longestStreak: number;
  showLongest?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function StreakDisplay({
  currentStreak,
  longestStreak,
  showLongest = true,
  size = 'md',
  className,
}: StreakDisplayProps) {
  const sizeClasses = {
    sm: { icon: 16, text: 'text-sm', gap: 'gap-1' },
    md: { icon: 20, text: 'text-base', gap: 'gap-2' },
    lg: { icon: 28, text: 'text-xl', gap: 'gap-3' },
  };

  const isActive = currentStreak > 0;
  const config = sizeClasses[size];

  return (
    <div className={cn('flex items-center', config.gap, className)}>
      <div className="relative">
        <Flame
          size={config.icon}
          className={cn(
            'transition-colors',
            isActive ? 'text-orange-500' : 'text-gray-300'
          )}
          fill={isActive ? 'currentColor' : 'none'}
        />
        {isActive && currentStreak >= 7 && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
        )}
      </div>
      <div className="flex flex-col">
        <span className={cn('font-bold', config.text, isActive ? 'text-orange-600' : 'text-gray-400')}>
          {currentStreak} day{currentStreak !== 1 ? 's' : ''}
        </span>
        {showLongest && longestStreak > 0 && (
          <span className="text-xs text-gray-500">
            Best: {longestStreak} day{longestStreak !== 1 ? 's' : ''}
          </span>
        )}
      </div>
    </div>
  );
}
