'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Edit, Trash2, MessageCircle, ChevronDown, ChevronUp, Mic } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import type { JournalEntry } from '@/types';
import { formatDate, getMoodEmoji, cn } from '@/lib/utils';

export default function EntryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [entry, setEntry] = useState<JournalEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);

  useEffect(() => {
    loadEntry();
  }, [params.id]);

  async function loadEntry() {
    try {
      const data = await api.getEntry(params.id as string);
      setEntry(data);
    } catch (error) {
      console.error('Failed to load entry:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await api.deleteEntry(params.id as string);
      router.push('/journal');
    } catch (error) {
      console.error('Failed to delete entry:', error);
    } finally {
      setDeleting(false);
    }
  }

  async function startChatAboutEntry() {
    try {
      const session = await api.createChatSession(params.id as string);
      router.push(`/chat?session=${session.id}`);
    } catch (error) {
      console.error('Failed to create chat session:', error);
    }
  }

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading entry...</div>;
  }

  if (!entry) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Entry not found.</p>
        <Link href="/journal" className="text-primary-600 hover:underline mt-2 inline-block">
          Back to Journal
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/journal">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={startChatAboutEntry}>
            <MessageCircle className="w-4 h-4 mr-2" />
            Discuss with AI
          </Button>
          <Link href={`/journal/${entry.id}/edit`}>
            <Button variant="outline" size="sm">
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
          </Link>
          <Button variant="danger" size="sm" onClick={() => setShowDeleteModal(true)}>
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="py-6">
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {entry.title || 'Untitled Entry'}
                  {entry.mood && <span className="ml-3">{getMoodEmoji(entry.mood)}</span>}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {formatDate(entry.created_at)}
                </p>
              </div>
            </div>

            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap text-gray-700">{entry.content}</p>
            </div>

            {entry.transcript && (
              <div className="border-t pt-4 mt-4">
                <button
                  onClick={() => setShowTranscript(!showTranscript)}
                  className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <Mic className="w-4 h-4" />
                  <span>Voice Conversation</span>
                  {showTranscript ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
                {showTranscript && (
                  <div className="mt-4 space-y-3">
                    {entry.transcript.split('\n\n').map((message, index) => {
                      const isUser = message.startsWith('You:');
                      const content = message.replace(/^(You|JournalBuddy):/, '').trim();
                      return (
                        <div
                          key={index}
                          className={cn(
                            'p-3 rounded-lg max-w-[85%]',
                            isUser
                              ? 'bg-primary-100 text-primary-900 ml-auto'
                              : 'bg-gray-100 text-gray-800'
                          )}
                        >
                          <p className="text-xs font-medium mb-1 opacity-70">
                            {isUser ? 'You' : 'JournalBuddy'}
                          </p>
                          <p className="text-sm">{content}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Entry"
      >
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete this journal entry? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
