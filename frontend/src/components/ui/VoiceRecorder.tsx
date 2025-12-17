'use client';

import { Mic, Square, Loader2 } from 'lucide-react';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import { Button } from './Button';
import { cn } from '@/lib/utils';

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  className?: string;
  disabled?: boolean;
}

function AmplitudeVisualizer({ amplitude }: { amplitude: number }) {
  const bars = 5;
  return (
    <div className="flex items-center gap-0.5 h-6">
      {Array.from({ length: bars }).map((_, i) => {
        const threshold = (i + 1) / bars;
        const isActive = amplitude >= threshold * 0.5;
        const height = 8 + (i * 3);
        return (
          <div
            key={i}
            className={cn(
              'w-1 rounded-full transition-all duration-75',
              isActive ? 'bg-red-500' : 'bg-gray-300'
            )}
            style={{
              height: isActive ? `${height + amplitude * 10}px` : `${height}px`,
            }}
          />
        );
      })}
    </div>
  );
}

export function VoiceRecorder({
  onTranscription,
  className,
  disabled = false,
}: VoiceRecorderProps) {
  const {
    isRecording,
    isProcessing,
    amplitude,
    startRecording,
    stopRecording,
    cancelRecording,
    error,
  } = useVoiceRecording();

  async function handleToggle() {
    if (isRecording) {
      const text = await stopRecording();
      if (text) {
        onTranscription(text);
      }
    } else {
      await startRecording();
    }
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Button
        type="button"
        variant={isRecording ? 'danger' : 'outline'}
        size="sm"
        onClick={handleToggle}
        disabled={disabled || isProcessing}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : isRecording ? (
          <>
            <Square className="w-4 h-4 mr-2" />
            Stop
          </>
        ) : (
          <>
            <Mic className="w-4 h-4 mr-2" />
            Voice Input
          </>
        )}
      </Button>
      {isRecording && (
        <>
          <AmplitudeVisualizer amplitude={amplitude} />
          <button
            type="button"
            onClick={cancelRecording}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Cancel
          </button>
        </>
      )}
      {error && <span className="text-sm text-red-500">{error}</span>}
    </div>
  );
}
