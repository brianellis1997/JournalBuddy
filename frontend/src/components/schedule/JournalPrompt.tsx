'use client';

import { Sunrise, Moon, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import type { ScheduleStatus } from '@/types';

interface JournalPromptProps {
  scheduleStatus: ScheduleStatus;
  className?: string;
}

export function JournalPrompt({ scheduleStatus, className }: JournalPromptProps) {
  const router = useRouter();

  const showMorning = scheduleStatus.should_show_morning;
  const showEvening = scheduleStatus.should_show_evening;
  const morningDone = scheduleStatus.morning_completed;
  const eveningDone = scheduleStatus.evening_completed;

  if (!showMorning && !showEvening && !morningDone && !eveningDone) {
    return null;
  }

  return (
    <div className={cn('bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100', className)}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          {showMorning && (
            <div className="flex items-center gap-2 mb-2">
              <Sunrise className="text-orange-500" size={24} />
              <h3 className="text-lg font-semibold text-gray-800">Time for your morning journal</h3>
            </div>
          )}
          {showEvening && (
            <div className="flex items-center gap-2 mb-2">
              <Moon className="text-indigo-500" size={24} />
              <h3 className="text-lg font-semibold text-gray-800">Time for your evening journal</h3>
            </div>
          )}
          {!showMorning && !showEvening && (morningDone || eveningDone) && (
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="text-green-500" size={24} />
              <h3 className="text-lg font-semibold text-gray-800">Great progress today!</h3>
            </div>
          )}
          <p className="text-gray-600 text-sm">
            {showMorning && scheduleStatus.morning_prompt}
            {showEvening && scheduleStatus.evening_prompt}
            {!showMorning && !showEvening && (morningDone && eveningDone
              ? "You've completed both journals for today."
              : morningDone
              ? "Morning journal done. Evening journal available later."
              : eveningDone
              ? "Evening journal complete!"
              : ""
            )}
          </p>
        </div>
        <div className="flex gap-2">
          {showMorning && (
            <Button
              onClick={() => router.push('/journal/new?type=morning')}
              className="flex items-center gap-2"
            >
              <Sunrise size={18} />
              Morning Journal
            </Button>
          )}
          {showEvening && (
            <Button
              onClick={() => router.push('/journal/new?type=evening')}
              className="flex items-center gap-2"
            >
              <Moon size={18} />
              Evening Journal
            </Button>
          )}
        </div>
      </div>
      <div className="flex gap-4 mt-4 pt-4 border-t border-blue-200">
        <div className="flex items-center gap-2">
          <Sunrise size={16} className={morningDone ? 'text-green-500' : 'text-gray-300'} />
          <span className={cn('text-sm', morningDone ? 'text-green-600' : 'text-gray-400')}>
            Morning {morningDone ? 'Done' : 'Pending'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Moon size={16} className={eveningDone ? 'text-green-500' : 'text-gray-300'} />
          <span className={cn('text-sm', eveningDone ? 'text-green-600' : 'text-gray-400')}>
            Evening {eveningDone ? 'Done' : 'Pending'}
          </span>
        </div>
      </div>
    </div>
  );
}
