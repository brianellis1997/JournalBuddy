'use client';

import { useState } from 'react';
import { Phone, History } from 'lucide-react';
import { VoiceChatInterface } from '@/components/voice/VoiceChatInterface';
import { VoiceSessionHistory } from '@/components/voice/VoiceSessionHistory';
import { cn } from '@/lib/utils';

type Tab = 'chat' | 'history';

export default function BuddyPage() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');

  return (
    <div className="h-[calc(100vh-4rem)] -m-6 flex flex-col">
      <div className="flex border-b border-gray-200 bg-white">
        <button
          onClick={() => setActiveTab('chat')}
          className={cn(
            'flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors',
            activeTab === 'chat'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          )}
        >
          <Phone className="w-4 h-4" />
          Voice Chat
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={cn(
            'flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors',
            activeTab === 'history'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          )}
        >
          <History className="w-4 h-4" />
          Past Sessions
        </button>
      </div>

      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? (
          <VoiceChatInterface />
        ) : (
          <div className="h-full overflow-y-auto p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Voice Session History
            </h2>
            <VoiceSessionHistory />
          </div>
        )}
      </div>
    </div>
  );
}
