'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, PenLine, MessageCircle, Mic, Send, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent } from '@/components/ui/Card';
import { VoiceRecorder } from '@/components/ui/VoiceRecorder';
import { JournalTypeSelector } from '@/components/schedule/JournalTypeSelector';
import { VoiceChatInterface } from '@/components/voice/VoiceChatInterface';
import { cn } from '@/lib/utils';
import type { JournalType } from '@/types';

type EntryMode = 'write' | 'chat' | 'voice';

const moods = [
  { value: 'great', emoji: '😊', label: 'Great' },
  { value: 'good', emoji: '🙂', label: 'Good' },
  { value: 'okay', emoji: '😐', label: 'Okay' },
  { value: 'bad', emoji: '😔', label: 'Bad' },
  { value: 'terrible', emoji: '😢', label: 'Terrible' },
];

const modes = [
  { value: 'write' as EntryMode, label: 'Write', icon: PenLine, description: 'Type your journal entry' },
  { value: 'chat' as EntryMode, label: 'Chat', icon: MessageCircle, description: 'Have a conversation' },
  { value: 'voice' as EntryMode, label: 'Voice', icon: Mic, description: 'Talk with JournalBuddy' },
];

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function NewEntryPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [mode, setMode] = useState<EntryMode>('write');
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [mood, setMood] = useState<string | undefined>();
  const [journalType, setJournalType] = useState<JournalType | undefined>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const streamingContentRef = useRef('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const typeParam = searchParams.get('type') as JournalType | null;
    if (typeParam && ['morning', 'evening', 'freeform'].includes(typeParam)) {
      setJournalType(typeParam);
    }
    const modeParam = searchParams.get('mode') as EntryMode | null;
    if (modeParam && ['write', 'chat', 'voice'].includes(modeParam)) {
      setMode(modeParam);
    }
  }, [searchParams]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, streamingMessage]);

  useEffect(() => {
    if (mode === 'chat' && !chatSessionId) {
      createChatSession();
    }
  }, [mode]);

  async function createChatSession() {
    try {
      const session = await api.createChatSession();
      setChatSessionId(session.id);
    } catch (err) {
      setError('Failed to start chat session');
    }
  }

  async function handleWriteSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) {
      setError('Please write something in your journal entry.');
      return;
    }

    setSaving(true);
    setError('');

    try {
      const entry = await api.createEntry({
        title: title.trim() || undefined,
        content: content.trim(),
        mood,
        journal_type: journalType,
      });
      router.push(`/journal/${entry.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save entry');
    } finally {
      setSaving(false);
    }
  }

  async function sendChatMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!chatInput.trim() || chatSending || !chatSessionId) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: chatInput.trim(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatSending(true);
    setStreamingMessage('');
    streamingContentRef.current = '';

    try {
      await api.sendMessageStream(
        chatSessionId,
        userMessage.content,
        (chunk) => {
          streamingContentRef.current += chunk;
          setStreamingMessage(streamingContentRef.current);
        },
        () => {
          const finalContent = streamingContentRef.current;
          if (finalContent) {
            setChatMessages(prev => [...prev, {
              id: Date.now().toString(),
              role: 'assistant',
              content: finalContent,
            }]);
          }
          setStreamingMessage('');
          streamingContentRef.current = '';
          setChatSending(false);
        },
        (error) => {
          console.error('Stream error:', error);
          setStreamingMessage('');
          streamingContentRef.current = '';
          setChatSending(false);
        }
      );
    } catch (err) {
      console.error('Failed to send message:', err);
      setChatSending(false);
    }
  }

  async function saveChatAsEntry() {
    if (chatMessages.length === 0) {
      setError('Have a conversation first before saving.');
      return;
    }

    setSaving(true);
    setError('');

    const conversationContent = chatMessages
      .map(m => `${m.role === 'user' ? 'Me' : 'JournalBuddy'}: ${m.content}`)
      .join('\n\n');

    try {
      const entry = await api.createEntry({
        title: title.trim() || `Chat on ${new Date().toLocaleDateString()}`,
        content: conversationContent,
        mood,
        journal_type: journalType,
      });
      router.push(`/journal/${entry.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save entry');
    } finally {
      setSaving(false);
    }
  }

  function handleChatKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (chatInput.trim() && !chatSending && chatSessionId) {
        sendChatMessage(e as unknown as React.FormEvent);
      }
    }
  }

  function adjustTextareaHeight() {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/journal">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          {journalType === 'morning' ? 'Morning Journal' :
           journalType === 'evening' ? 'Evening Journal' :
           'New Journal Entry'}
        </h1>
      </div>

      <div className="flex gap-2 p-1 bg-gray-100 rounded-xl">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => setMode(m.value)}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg transition-all font-medium',
              mode === m.value
                ? 'bg-white shadow-sm text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <m.icon className="w-5 h-5" />
            <span>{m.label}</span>
          </button>
        ))}
      </div>

      {mode === 'write' && (
        <Card>
          <CardContent className="py-6">
            <form onSubmit={handleWriteSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Journal Type
                </label>
                <JournalTypeSelector
                  value={journalType}
                  onChange={setJournalType}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Title (optional)
                </label>
                <Input
                  type="text"
                  placeholder="Give your entry a title..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  How are you feeling?
                </label>
                <div className="flex gap-2">
                  {moods.map((m) => (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setMood(mood === m.value ? undefined : m.value)}
                      className={cn(
                        'flex flex-col items-center gap-1 p-3 rounded-lg border transition-colors',
                        mood === m.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300'
                      )}
                    >
                      <span className="text-2xl">{m.emoji}</span>
                      <span className="text-xs text-gray-600">{m.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    What's on your mind?
                  </label>
                  <VoiceRecorder
                    onTranscription={(text) => {
                      setContent((prev) => (prev ? `${prev}\n\n${text}` : text));
                    }}
                    disabled={saving}
                  />
                </div>
                <Textarea
                  placeholder="Write your thoughts, feelings, or anything you want to remember..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={10}
                />
              </div>

              <div className="flex justify-end gap-3">
                <Link href="/journal">
                  <Button variant="outline" type="button">
                    Cancel
                  </Button>
                </Link>
                <Button type="submit" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Entry'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {mode === 'chat' && (
        <Card className="overflow-hidden -mx-6 -mb-6 rounded-none border-x-0 border-b-0">
          <CardContent className="p-0">
            <div className="flex flex-col h-[calc(100vh-12rem)]">
              <div className="p-4 border-b bg-gray-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">Chat with JournalBuddy</p>
                    <p className="text-sm text-gray-500">Have a conversation, then save it as an entry</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <JournalTypeSelector
                      value={journalType}
                      onChange={setJournalType}
                      compact
                    />
                  </div>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.length === 0 && !streamingMessage && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">
                      Hi! I'm JournalBuddy. Tell me about your day, what's on your mind, or anything you'd like to reflect on.
                    </p>
                  </div>
                )}

                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={cn(
                        'max-w-[80%] rounded-xl px-4 py-2',
                        message.role === 'user'
                          ? 'bg-primary-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      )}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}

                {streamingMessage && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-xl px-4 py-2 bg-gray-100 text-gray-900">
                      <p className="whitespace-pre-wrap">{streamingMessage}</p>
                    </div>
                  </div>
                )}

                {chatSending && !streamingMessage && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-xl px-4 py-2">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="p-4 border-t bg-white">
                {error && (
                  <div className="bg-red-50 text-red-600 p-2 rounded-md text-sm mb-3">
                    {error}
                  </div>
                )}
                <form onSubmit={sendChatMessage} className="flex gap-2 items-end">
                  <textarea
                    ref={textareaRef}
                    value={chatInput}
                    onChange={(e) => {
                      setChatInput(e.target.value);
                      adjustTextareaHeight();
                    }}
                    onKeyDown={handleChatKeyDown}
                    placeholder="Type your message... (Enter to send)"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none min-h-[42px] max-h-[100px]"
                    disabled={chatSending || !chatSessionId}
                    rows={1}
                  />
                  <Button type="submit" disabled={chatSending || !chatInput.trim() || !chatSessionId}>
                    {chatSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  </Button>
                </form>
              </div>

              {chatMessages.length > 0 && (
                <div className="p-4 border-t bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-600">Mood:</span>
                    <div className="flex gap-1">
                      {moods.map((m) => (
                        <button
                          key={m.value}
                          type="button"
                          onClick={() => setMood(mood === m.value ? undefined : m.value)}
                          className={cn(
                            'p-2 rounded-lg border transition-colors',
                            mood === m.value
                              ? 'border-primary-500 bg-primary-50'
                              : 'border-transparent hover:bg-gray-100'
                          )}
                          title={m.label}
                        >
                          <span className="text-lg">{m.emoji}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <Button onClick={saveChatAsEntry} disabled={saving}>
                    {saving ? 'Saving...' : 'Save as Entry'}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {mode === 'voice' && (
        <Card className="overflow-hidden -mx-6 -mb-6 rounded-none border-x-0 border-b-0">
          <CardContent className="p-0">
            <div className="h-[calc(100vh-12rem)]">
              <VoiceChatInterface journalType={journalType === 'freeform' ? undefined : journalType} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
