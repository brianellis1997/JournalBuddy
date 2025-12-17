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

export function VoiceRecorder({
  onTranscription,
  className,
  disabled = false,
}: VoiceRecorderProps) {
  const {
    isRecording,
    isProcessing,
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
        className={cn(
          'relative',
          isRecording && 'animate-pulse'
        )}
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : isRecording ? (
          <>
            <Square className="w-4 h-4 mr-2" />
            Stop Recording
          </>
        ) : (
          <>
            <Mic className="w-4 h-4 mr-2" />
            Voice Input
          </>
        )}
      </Button>
      {isRecording && (
        <button
          type="button"
          onClick={cancelRecording}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Cancel
        </button>
      )}
      {error && <span className="text-sm text-red-500">{error}</span>}
    </div>
  );
}
