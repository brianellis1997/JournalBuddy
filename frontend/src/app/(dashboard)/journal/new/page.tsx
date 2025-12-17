'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent } from '@/components/ui/Card';
import { VoiceRecorder } from '@/components/ui/VoiceRecorder';
import { cn } from '@/lib/utils';

const moods = [
  { value: 'great', emoji: '😊', label: 'Great' },
  { value: 'good', emoji: '🙂', label: 'Good' },
  { value: 'okay', emoji: '😐', label: 'Okay' },
  { value: 'bad', emoji: '😔', label: 'Bad' },
  { value: 'terrible', emoji: '😢', label: 'Terrible' },
];

export default function NewEntryPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [mood, setMood] = useState<string | undefined>();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
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
      });
      router.push(`/journal/${entry.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save entry');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-4">
        <Link href="/journal">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">New Journal Entry</h1>
      </div>

      <Card>
        <CardContent className="py-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                {error}
              </div>
            )}

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
                placeholder="Write your thoughts, feelings, or anything you want to remember... or use voice input above"
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
    </div>
  );
}
