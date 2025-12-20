'use client';

import {
  Pencil,
  Book,
  BookOpen,
  Trophy,
  Flame,
  Target,
  CheckCircle,
  Star,
  Sunrise,
  Moon,
  Crown,
  Medal,
  Lock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Achievement } from '@/types';

const iconMap: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  pencil: Pencil,
  book: Book,
  'book-open': BookOpen,
  trophy: Trophy,
  flame: Flame,
  fire: Flame,
  target: Target,
  'check-circle': CheckCircle,
  star: Star,
  sunrise: Sunrise,
  moon: Moon,
  crown: Crown,
  medal: Medal,
};

interface AchievementCardProps {
  achievement: Achievement;
  size?: 'sm' | 'md';
  className?: string;
}

export function AchievementCard({ achievement, size = 'md', className }: AchievementCardProps) {
  const isUnlocked = !!achievement.unlocked_at;
  const progress = achievement.progress ?? 0;
  const target = achievement.target ?? 1;
  const progressPercent = Math.min((progress / target) * 100, 100);

  const Icon = iconMap[achievement.icon] || Star;

  const sizeClasses = {
    sm: {
      card: 'p-3',
      icon: 24,
      title: 'text-sm',
      desc: 'text-xs',
    },
    md: {
      card: 'p-4',
      icon: 32,
      title: 'text-base',
      desc: 'text-sm',
    },
  };

  const config = sizeClasses[size];

  return (
    <div
      className={cn(
        'relative rounded-lg border transition-all',
        isUnlocked
          ? 'bg-gradient-to-br from-purple-50 to-white border-purple-200 shadow-sm'
          : 'bg-gray-50 border-gray-200',
        config.card,
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'rounded-full p-2 flex-shrink-0',
            isUnlocked ? 'bg-purple-100 text-purple-600' : 'bg-gray-200 text-gray-400'
          )}
        >
          {isUnlocked ? (
            <Icon size={config.icon} />
          ) : (
            <Lock size={config.icon} />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h4
            className={cn(
              'font-semibold truncate',
              config.title,
              isUnlocked ? 'text-gray-900' : 'text-gray-500'
            )}
          >
            {achievement.name}
          </h4>
          <p
            className={cn(
              'mt-0.5 line-clamp-2',
              config.desc,
              isUnlocked ? 'text-gray-600' : 'text-gray-400'
            )}
          >
            {achievement.description}
          </p>
          {!isUnlocked && target > 1 && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{progress} / {target}</span>
                <span>{Math.round(progressPercent)}%</span>
              </div>
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-purple-400 rounded-full transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      {isUnlocked && (
        <div className="absolute top-2 right-2">
          <CheckCircle size={16} className="text-green-500" />
        </div>
      )}
    </div>
  );
}
