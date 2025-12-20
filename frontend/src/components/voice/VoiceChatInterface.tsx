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

interface VoiceChatInterfaceProps {
  journalType?: 'morning' | 'evening';
}

export function VoiceChatInterface({ journalType }: VoiceChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentUserTranscript, setCurrentUserTranscript] = useState('');
  const [currentAssistantText, setCurrentAssistantText] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const assistantTextRef = useRef('');

  const {
    state,
    isConnected,
    amplitude,
    conversationEnded,
    start,
    disconnect,
    interrupt,
  } = useVoiceChat({
    journalType,
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
      console.log('[Interface] onAssistantText called:', { text: text.substring(0, 30), isFinal, refLength: assistantTextRef.current.length });
      if (!isFinal) {
        assistantTextRef.current += text;
        setCurrentAssistantText(assistantTextRef.current);
        console.log('[Interface] Updated assistantTextRef:', assistantTextRef.current.substring(0, 50));
      } else {
        console.log('[Interface] isFinal=true, ref content:', assistantTextRef.current.substring(0, 50));
        if (assistantTextRef.current.trim()) {
          const content = assistantTextRef.current.trim();
          console.log('[Interface] Adding message to list:', content.substring(0, 50));
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: content,
            timestamp: new Date(),
          }]);
        } else {
          console.log('[Interface] assistantTextRef was empty, not adding message');
        }
        assistantTextRef.current = '';
        setCurrentAssistantText('');
      }
    },
    onError: (errorMsg) => {
      setError(errorMsg);
      setTimeout(() => setError(null), 5000);
    },
    onConversationEnd: () => {
      setTimeout(() => {
        disconnect();
      }, 3000);
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
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-50 to-white">
      {state === 'disconnected' ? (
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <JournalBuddyAvatar state={state} size="lg" />
          <div className="mt-12 text-center max-w-md">
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
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm text-center max-w-md">
              {error}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between p-4 border-b bg-white">
            <div className="flex items-center gap-3">
              <JournalBuddyAvatar state={state} size="sm" />
              <div>
                <p className="font-medium text-gray-900">JournalBuddy</p>
                <p className="text-sm text-gray-500">
                  {conversationEnded ? 'Conversation complete' :
                   state === 'listening' ? 'Listening...' :
                   state === 'thinking' ? 'Thinking...' :
                   state === 'speaking' ? 'Speaking...' :
                   'Ready to chat'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMuted(!isMuted)}
                className={cn('h-9 w-9 p-0', isMuted && 'bg-red-50 border-red-200')}
              >
                {isMuted ? <MicOff className="w-4 h-4 text-red-500" /> : <Mic className="w-4 h-4" />}
              </Button>
              {state === 'speaking' && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleInterrupt}
                  className="h-9 px-3 gap-1"
                >
                  <VolumeX className="w-4 h-4" />
                  Stop
                </Button>
              )}
              <Button
                variant="danger"
                size="sm"
                onClick={handleEndCall}
                className="h-9 px-3 gap-1"
              >
                <PhoneOff className="w-4 h-4" />
                End
              </Button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="max-w-2xl mx-auto space-y-4">
              {messages.length === 0 && !currentUserTranscript && !currentAssistantText && state !== 'thinking' && (
                <p className="text-gray-400 text-center text-sm py-8">
                  Speak to start the conversation...
                </p>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    'p-4 rounded-xl max-w-[85%]',
                    message.role === 'user'
                      ? 'bg-primary-500 text-white ml-auto'
                      : 'bg-white border border-gray-200 shadow-sm'
                  )}
                >
                  <p className={message.role === 'user' ? 'text-white' : 'text-gray-800'}>
                    {message.content}
                  </p>
                </div>
              ))}

              {currentUserTranscript && (
                <div className="p-4 rounded-xl max-w-[85%] ml-auto bg-primary-200 text-primary-900">
                  <p>{currentUserTranscript}</p>
                </div>
              )}

              {state === 'thinking' && !currentAssistantText && (
                <div className="p-4 rounded-xl max-w-[85%] bg-white border border-gray-200 shadow-sm">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              )}

              {currentAssistantText && (
                <div className="p-4 rounded-xl max-w-[85%] bg-white border border-gray-200 shadow-sm">
                  <p className="text-gray-800">{currentAssistantText}</p>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>

          <div className="p-4 border-t bg-white">
            <div className="flex items-center justify-center gap-4">
              {(state === 'listening' || state === 'idle') && !conversationEnded && (
                <AmplitudeVisualizer amplitude={amplitude} />
              )}
              <p className="text-sm text-gray-500">
                {conversationEnded && 'Disconnecting...'}
                {!conversationEnded && state === 'listening' && 'Listening...'}
                {!conversationEnded && state === 'thinking' && 'Processing...'}
                {!conversationEnded && state === 'speaking' && 'Speaking...'}
                {!conversationEnded && state === 'idle' && 'Say something to continue'}
              </p>
              {(state === 'listening' || state === 'idle') && !conversationEnded && (
                <AmplitudeVisualizer amplitude={amplitude} />
              )}
            </div>
          </div>

          {error && (
            <div className="absolute bottom-20 left-1/2 -translate-x-1/2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}
        </>
      )}
    </div>
  );
}
