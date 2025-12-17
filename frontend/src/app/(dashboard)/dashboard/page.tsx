'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, TrendingUp, BookOpen, Target, Flame } from 'lucide-react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { Metrics, JournalEntry, Goal } from '@/types';
import { formatRelativeDate, getMoodEmoji, truncate } from '@/lib/utils';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [recentEntries, setRecentEntries] = useState<JournalEntry[]>([]);
  const [activeGoals, setActiveGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [metricsData, entriesData, goalsData] = await Promise.all([
          api.getMetrics(),
          api.getEntries(1, 5),
          api.getGoals('active'),
        ]);
        setMetrics(metricsData);
        setRecentEntries(entriesData.entries);
        setActiveGoals(goalsData.slice(0, 3));
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link href="/journal/new">
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Entry
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="flex items-center gap-4 py-6">
            <div className="p-3 bg-orange-100 rounded-lg">
              <Flame className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics?.current_streak || 0}</p>
              <p className="text-sm text-gray-500">Day streak</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 py-6">
            <div className="p-3 bg-blue-100 rounded-lg">
              <BookOpen className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics?.total_entries || 0}</p>
              <p className="text-sm text-gray-500">Total entries</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 py-6">
            <div className="p-3 bg-green-100 rounded-lg">
              <Target className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics?.active_goals || 0}</p>
              <p className="text-sm text-gray-500">Active goals</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex items-center gap-4 py-6">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{metrics?.entries_this_week || 0}</p>
              <p className="text-sm text-gray-500">This week</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent Entries</h2>
              <Link href="/journal" className="text-sm text-primary-600 hover:underline">
                View all
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentEntries.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No entries yet. Start journaling!</p>
            ) : (
              recentEntries.map((entry) => (
                <Link
                  key={entry.id}
                  href={`/journal/${entry.id}`}
                  className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900">
                        {entry.title || 'Untitled'}
                        {entry.mood && <span className="ml-2">{getMoodEmoji(entry.mood)}</span>}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {truncate(entry.content, 100)}
                      </p>
                    </div>
                    <span className="text-xs text-gray-400 whitespace-nowrap ml-4">
                      {formatRelativeDate(entry.created_at)}
                    </span>
                  </div>
                </Link>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Active Goals</h2>
              <Link href="/goals" className="text-sm text-primary-600 hover:underline">
                View all
              </Link>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {activeGoals.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No active goals. Set some goals!</p>
            ) : (
              activeGoals.map((goal) => (
                <Link
                  key={goal.id}
                  href={`/goals/${goal.id}`}
                  className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <p className="font-medium text-gray-900">{goal.title}</p>
                  {goal.description && (
                    <p className="text-sm text-gray-500 mt-1">
                      {truncate(goal.description, 80)}
                    </p>
                  )}
                  {goal.target_date && (
                    <p className="text-xs text-gray-400 mt-2">
                      Target: {new Date(goal.target_date).toLocaleDateString()}
                    </p>
                  )}
                </Link>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
