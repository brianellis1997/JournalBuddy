'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Phone, PhoneOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { JournalBuddyAvatar } from './JournalBuddyAvatar';
import { useVoiceChat, VoiceChatState } from '@/hooks/useVoiceChat';
import { cn } from '@/lib/utils';

function AmplitudeVisualizer({ amplitude }: { amplitude: number }) {
  const bars = 5;
  return (
    <div className="flex items-center gap-1 h-8">
      {Array.from({ length: bars }).map((_, i) => {
        const threshold = (i + 1) / bars;
        const isActive = amplitude >= threshold * 0.5;
        const baseHeight = 12 + (i * 4);
        return (
          <div
            key={i}
            className={cn(
              'w-1.5 rounded-full transition-all duration-75',
              isActive ? 'bg-primary-500' : 'bg-gray-300'
            )}
            style={{
              height: isActive ? `${baseHeight + amplitude * 16}px` : `${baseHeight}px`,
            }}
          />
        );
      })}
    </div>
  );
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function VoiceChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentUserTranscript, setCurrentUserTranscript] = useState('');
  const [currentAssistantText, setCurrentAssistantText] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    state,
    isConnected,
    amplitude,
    start,
    disconnect,
    interrupt,
  } = useVoiceChat({
    onTranscript: (text, isFinal) => {
      setCurrentUserTranscript(text);
      if (isFinal && text.trim()) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'user',
          content: text.trim(),
          timestamp: new Date(),
        }]);
        setCurrentUserTranscript('');
      }
    },
    onAssistantText: (text, isFinal) => {
      if (!isFinal) {
        setCurrentAssistantText(prev => prev + text);
      } else {
        if (currentAssistantText.trim()) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: currentAssistantText.trim(),
            timestamp: new Date(),
          }]);
        }
        setCurrentAssistantText('');
      }
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, currentAssistantText]);

  const handleStartCall = async () => {
    setError(null);
    await start();
  };

  const handleEndCall = () => {
    disconnect();
    setMessages([]);
    setCurrentUserTranscript('');
    setCurrentAssistantText('');
  };

  const handleInterrupt = () => {
    if (state === 'speaking') {
      interrupt();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        <JournalBuddyAvatar state={state} size="lg" />

        <div className="mt-16 w-full max-w-2xl">
          {state === 'disconnected' ? (
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Talk with JournalBuddy
              </h2>
              <p className="text-gray-600 mb-8">
                Start a voice conversation with your AI journaling companion.
                Share your thoughts, reflect on your day, or just chat.
              </p>
              <Button size="lg" onClick={handleStartCall} className="gap-2">
                <Phone className="w-5 h-5" />
                Start Conversation
              </Button>
            </div>
          ) : (
            <>
              <div className="bg-white rounded-xl shadow-lg border border-gray-200 max-h-64 overflow-y-auto p-4 mb-4">
                {messages.length === 0 && !currentUserTranscript && !currentAssistantText && state !== 'thinking' && (
                  <p className="text-gray-400 text-center text-sm">
                    Conversation will appear here...
                  </p>
                )}

                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'mb-3 p-3 rounded-lg',
                      message.role === 'user'
                        ? 'bg-primary-50 ml-8'
                        : 'bg-gray-50 mr-8'
                    )}
                  >
                    <p className="text-xs text-gray-400 mb-1">
                      {message.role === 'user' ? 'You' : 'JournalBuddy'}
                    </p>
                    <p className="text-gray-800">{message.content}</p>
                  </div>
                ))}

                {currentUserTranscript && (
                  <div className="mb-3 p-3 rounded-lg bg-primary-50 ml-8 opacity-70">
                    <p className="text-xs text-gray-400 mb-1">You (listening...)</p>
                    <p className="text-gray-800">{currentUserTranscript}</p>
                  </div>
                )}

                {(currentAssistantText || state === 'thinking') && (
                  <div className="mb-3 p-3 rounded-lg bg-gray-50 mr-8">
                    <p className="text-xs text-gray-400 mb-1">JournalBuddy</p>
                    {state === 'thinking' && !currentAssistantText ? (
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    ) : (
                      <p className="text-gray-800">{currentAssistantText}</p>
                    )}
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="flex justify-center gap-4">
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => setIsMuted(!isMuted)}
                  className={cn(isMuted && 'bg-red-50 border-red-200')}
                >
                  {isMuted ? <MicOff className="w-5 h-5 text-red-500" /> : <Mic className="w-5 h-5" />}
                </Button>

                {state === 'speaking' && (
                  <Button
                    variant="outline"
                    size="lg"
                    onClick={handleInterrupt}
                    className="gap-2"
                  >
                    <VolumeX className="w-5 h-5" />
                    Interrupt
                  </Button>
                )}

                <Button
                  variant="danger"
                  size="lg"
                  onClick={handleEndCall}
                  className="gap-2"
                >
                  <PhoneOff className="w-5 h-5" />
                  End
                </Button>
              </div>
            </>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm text-center">
              {error}
            </div>
          )}
        </div>
      </div>

      {isConnected && (
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-center gap-4">
            {(state === 'listening' || state === 'idle') && (
              <AmplitudeVisualizer amplitude={amplitude} />
            )}
            <p className="text-sm text-gray-500">
              {state === 'listening' && 'Listening to you...'}
              {state === 'thinking' && 'JournalBuddy is thinking...'}
              {state === 'speaking' && 'JournalBuddy is speaking... (click Interrupt to stop)'}
              {state === 'idle' && 'Say something to continue the conversation'}
            </p>
            {(state === 'listening' || state === 'idle') && (
              <AmplitudeVisualizer amplitude={amplitude} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
