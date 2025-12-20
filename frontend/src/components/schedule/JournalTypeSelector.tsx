'use client';

import { Sunrise, Moon, Pencil } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { JournalType } from '@/types';

interface JournalTypeSelectorProps {
  value?: JournalType;
  onChange: (type: JournalType) => void;
  className?: string;
  compact?: boolean;
}

const journalTypes: { value: JournalType; label: string; icon: React.ComponentType<{ size?: number; className?: string }>; color: string }[] = [
  { value: 'morning', label: 'Morning', icon: Sunrise, color: 'text-orange-500 bg-orange-50 border-orange-200' },
  { value: 'evening', label: 'Evening', icon: Moon, color: 'text-indigo-500 bg-indigo-50 border-indigo-200' },
  { value: 'freeform', label: 'Freeform', icon: Pencil, color: 'text-gray-500 bg-gray-50 border-gray-200' },
];

export function JournalTypeSelector({ value, onChange, className, compact }: JournalTypeSelectorProps) {
  return (
    <div className={cn('flex gap-2', className)}>
      {journalTypes.map((type) => {
        const Icon = type.icon;
        const isSelected = value === type.value;
        return (
          <button
            key={type.value}
            type="button"
            onClick={() => onChange(type.value)}
            className={cn(
              'flex items-center gap-2 rounded-lg border-2 transition-all',
              compact ? 'px-2 py-1' : 'px-4 py-2',
              isSelected
                ? type.color + ' border-current'
                : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
            )}
          >
            <Icon size={compact ? 14 : 18} />
            {!compact && <span className="font-medium">{type.label}</span>}
          </button>
        );
      })}
    </div>
  );
}
