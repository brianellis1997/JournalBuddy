'use client';

import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { MessageSquare, ChevronDown, ChevronUp, Clock, Target } from 'lucide-react';
import { api } from '@/lib/api';
import type { VoiceSession } from '@/types';
import { cn } from '@/lib/utils';

interface VoiceSessionCardProps {
  session: VoiceSession;
}

function VoiceSessionCard({ session }: VoiceSessionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const topics = session.key_topics?.split(',').map(t => t.trim()).filter(Boolean) || [];
  const goalUpdates = session.goal_updates?.split(',').map(g => g.trim()).filter(Boolean) || [];

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-primary-600" />
          </div>
          <div className="text-left">
            <p className="font-medium text-gray-900">
              {format(new Date(session.created_at), 'MMMM d, yyyy')}
            </p>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {format(new Date(session.created_at), 'h:mm a')}
              <span className="mx-1">•</span>
              {session.message_count} messages
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          {session.summary && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Summary</h4>
              <p className="text-gray-600 text-sm">{session.summary}</p>
            </div>
          )}

          {topics.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Topics Discussed</h4>
              <div className="flex flex-wrap gap-2">
                {topics.map((topic, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {goalUpdates.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                <Target className="w-4 h-4" />
                Goal Updates
              </h4>
              <div className="flex flex-wrap gap-2">
                {goalUpdates.map((update, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full"
                  >
                    {update}
                  </span>
                ))}
              </div>
            </div>
          )}

          {!session.summary && topics.length === 0 && goalUpdates.length === 0 && (
            <p className="mt-4 text-sm text-gray-400 italic">
              No summary available for this session.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function VoiceSessionHistory() {
  const [sessions, setSessions] = useState<VoiceSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await api.getVoiceSessions(10);
        setSessions(data);
      } catch (err) {
        setError('Failed to load voice sessions');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, []);

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gray-200" />
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-32" />
                <div className="h-3 bg-gray-200 rounded w-24" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600 text-sm">
        {error}
      </div>
    );
  }

  if (sessions.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No voice sessions yet.</p>
        <p className="text-gray-400 text-sm mt-1">
          Start a conversation with JournalBuddy above!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <VoiceSessionCard key={session.id} session={session} />
      ))}
    </div>
  );
}
