'use client';

import { Brain, Target, BookOpen, LogOut, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ToolCall } from '@/hooks/useVoiceChat';

const toolConfig: Record<string, { icon: React.ComponentType<{ className?: string }>; label: string; color: string }> = {
  recall_memory: {
    icon: Brain,
    label: 'Searching memories',
    color: 'bg-purple-100 text-purple-700 border-purple-200',
  },
  create_journal_entry: {
    icon: BookOpen,
    label: 'Creating entry',
    color: 'bg-blue-100 text-blue-700 border-blue-200',
  },
  update_goal_progress: {
    icon: Target,
    label: 'Updating goal',
    color: 'bg-green-100 text-green-700 border-green-200',
  },
  end_conversation: {
    icon: LogOut,
    label: 'Ending conversation',
    color: 'bg-gray-100 text-gray-700 border-gray-200',
  },
};

interface ToolActivityPillProps {
  toolCall: ToolCall;
  className?: string;
}

export function ToolActivityPill({ toolCall, className }: ToolActivityPillProps) {
  const config = toolConfig[toolCall.tool] || {
    icon: Loader2,
    label: toolCall.tool,
    color: 'bg-gray-100 text-gray-700 border-gray-200',
  };
  const Icon = config.icon;

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border animate-in fade-in slide-in-from-bottom-2 duration-300',
        config.color,
        className
      )}
    >
      <Icon className={cn('w-3 h-3', toolCall.status === 'start' && 'animate-pulse')} />
      <span>{config.label}</span>
      {toolCall.status === 'start' && (
        <Loader2 className="w-3 h-3 animate-spin" />
      )}
    </div>
  );
}

interface ToolActivityDisplayProps {
  activeTools: ToolCall[];
  className?: string;
}

export function ToolActivityDisplay({ activeTools, className }: ToolActivityDisplayProps) {
  if (activeTools.length === 0) return null;

  return (
    <div className={cn('flex flex-wrap gap-2 justify-center', className)}>
      {activeTools.map((tool, index) => (
        <ToolActivityPill key={`${tool.tool}-${index}`} toolCall={tool} />
      ))}
    </div>
  );
}
