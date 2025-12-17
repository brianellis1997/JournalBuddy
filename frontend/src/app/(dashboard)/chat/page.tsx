'use client';

import { useEffect, useState, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { Send, Plus, Trash2, Mic, Square, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import type { ChatSession, ChatMessage } from '@/types';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingContentRef = useRef('');
  const { isRecording, isProcessing, startRecording, stopRecording, cancelRecording, error: voiceError } = useVoiceRecording();

  async function handleVoiceToggle() {
    if (isRecording) {
      const text = await stopRecording();
      if (text) {
        setInput((prev) => (prev ? `${prev} ${text}` : text));
      }
    } else {
      await startRecording();
    }
  }

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    const sessionId = searchParams.get('session');
    if (sessionId && sessions.length > 0) {
      const session = sessions.find((s) => s.id === sessionId);
      if (session) {
        loadSession(sessionId);
      }
    }
  }, [searchParams, sessions]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  function scrollToBottom() {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }

  async function loadSessions() {
    try {
      const data = await api.getChatSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  }

  async function loadSession(sessionId: string) {
    try {
      const data = await api.getChatSession(sessionId);
      setCurrentSession(data);
      setMessages(data.messages);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  }

  async function createNewSession() {
    try {
      const session = await api.createChatSession();
      setSessions([session, ...sessions]);
      setCurrentSession(session);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  }

  async function deleteSession(sessionId: string) {
    try {
      await api.deleteChatSession(sessionId);
      setSessions(sessions.filter((s) => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  }

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending || !currentSession) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSending(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    try {
      await api.sendMessageStream(
        currentSession.id,
        userMessage.content,
        (chunk) => {
          streamingContentRef.current += chunk;
          setStreamingMessage(streamingContentRef.current);
        },
        () => {
          const finalContent = streamingContentRef.current;
          if (finalContent) {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                role: 'assistant',
                content: finalContent,
                created_at: new Date().toISOString(),
              },
            ]);
          }
          setStreamingMessage('');
          streamingContentRef.current = '';
          setSending(false);
        },
        (error) => {
          console.error('Stream error:', error);
          setStreamingMessage('');
          streamingContentRef.current = '';
          setSending(false);
        }
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setSending(false);
    }
  }

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading chat...</div>;
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      <div className="w-64 flex-shrink-0">
        <Card className="h-full flex flex-col">
          <div className="p-4 border-b">
            <Button onClick={createNewSession} className="w-full">
              <Plus className="w-4 h-4 mr-2" />
              New Chat
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {sessions.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No chats yet</p>
            ) : (
              <div className="space-y-1">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={cn(
                      'flex items-center justify-between p-3 rounded-lg cursor-pointer group',
                      currentSession?.id === session.id
                        ? 'bg-primary-50 text-primary-700'
                        : 'hover:bg-gray-100'
                    )}
                    onClick={() => loadSession(session.id)}
                  >
                    <span className="text-sm truncate">
                      {new Date(session.created_at).toLocaleDateString()}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      <Card className="flex-1 flex flex-col">
        {!currentSession ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Start a conversation
              </h2>
              <p className="text-gray-500 mb-4">
                Chat with your AI journaling companion
              </p>
              <Button onClick={createNewSession}>
                <Plus className="w-4 h-4 mr-2" />
                New Chat
              </Button>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 && !streamingMessage && (
                <div className="text-center py-8">
                  <p className="text-gray-500">
                    Hi! I'm your journaling companion. How can I help you reflect today?
                  </p>
                </div>
              )}

              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    'flex',
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  <div
                    className={cn(
                      'max-w-[80%] rounded-lg px-4 py-2',
                      message.role === 'user'
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              ))}

              {streamingMessage && (
                <div className="flex justify-start">
                  <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-100 text-gray-900">
                    <p className="whitespace-pre-wrap">{streamingMessage}</p>
                  </div>
                </div>
              )}

              {sending && !streamingMessage && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-4 py-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <form onSubmit={sendMessage} className="p-4 border-t">
              {voiceError && (
                <div className="text-sm text-red-500 mb-2">{voiceError}</div>
              )}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={isRecording ? 'Recording... click mic to stop' : 'Type your message or use voice input...'}
                  className={cn(
                    'flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500',
                    isRecording ? 'border-red-300 bg-red-50' : 'border-gray-300'
                  )}
                  disabled={sending || isRecording || isProcessing}
                />
                <Button
                  type="button"
                  variant={isRecording ? 'danger' : 'outline'}
                  onClick={handleVoiceToggle}
                  disabled={sending || isProcessing}
                  className={cn(isRecording && 'animate-pulse')}
                >
                  {isProcessing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : isRecording ? (
                    <Square className="w-4 h-4" />
                  ) : (
                    <Mic className="w-4 h-4" />
                  )}
                </Button>
                <Button type="submit" disabled={sending || !input.trim() || isRecording || isProcessing}>
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              {isRecording && (
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-sm text-red-500">Recording...</span>
                  <button
                    type="button"
                    onClick={cancelRecording}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </form>
          </>
        )}
      </Card>
    </div>
  );
}
