'use client';

import { cn } from '@/lib/utils';

interface LevelBadgeProps {
  level: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LevelBadge({ level, size = 'md', className }: LevelBadgeProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-lg',
  };

  const bgColor = level >= 10 ? 'bg-yellow-500' : level >= 5 ? 'bg-purple-500' : 'bg-blue-500';

  return (
    <div
      className={cn(
        'rounded-full flex items-center justify-center font-bold text-white shadow-lg',
        bgColor,
        sizeClasses[size],
        className
      )}
    >
      {level}
    </div>
  );
}
