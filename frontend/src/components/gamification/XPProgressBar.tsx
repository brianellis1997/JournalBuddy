'use client';

import { cn } from '@/lib/utils';

interface XPProgressBarProps {
  currentXP: number;
  xpForNextLevel: number;
  xpProgressInLevel: number;
  level: number;
  className?: string;
}

export function XPProgressBar({
  currentXP,
  xpForNextLevel,
  xpProgressInLevel,
  level,
  className,
}: XPProgressBarProps) {
  const progressPercent = Math.min((xpProgressInLevel / xpForNextLevel) * 100, 100);

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-purple-600">Level {level}</span>
          <span className="text-gray-500">{currentXP.toLocaleString()} XP</span>
        </div>
        <span className="text-gray-500">
          {xpProgressInLevel} / {xpForNextLevel} XP
        </span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
}
