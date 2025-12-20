'use client';

import { useEffect, useState } from 'react';
import { Calendar, TrendingUp, TrendingDown, Minus, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { AutoSummary } from '@/types';
import { formatDate } from '@/lib/utils';

function getMoodTrendIcon(trend?: string) {
  switch (trend) {
    case 'improving':
      return <TrendingUp className="w-5 h-5 text-green-500" />;
    case 'declining':
      return <TrendingDown className="w-5 h-5 text-red-500" />;
    case 'mixed':
      return <Sparkles className="w-5 h-5 text-purple-500" />;
    default:
      return <Minus className="w-5 h-5 text-gray-400" />;
  }
}

function getMoodTrendLabel(trend?: string) {
  switch (trend) {
    case 'improving':
      return 'Improving';
    case 'declining':
      return 'Declining';
    case 'mixed':
      return 'Mixed';
    default:
      return 'Stable';
  }
}

function SummaryCard({ summary }: { summary: AutoSummary }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="py-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-700 mb-2">
              {summary.period_type === 'weekly' ? 'Weekly' : 'Monthly'} Summary
            </span>
            <h3 className="text-lg font-semibold text-gray-900">{summary.title}</h3>
            <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
              <Calendar className="w-4 h-4" />
              <span>
                {formatDate(summary.period_start)} - {formatDate(summary.period_end)}
              </span>
              <span className="text-gray-300">|</span>
              <span>{summary.entry_count} entries</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getMoodTrendIcon(summary.mood_trend)}
            <span className="text-sm text-gray-600">{getMoodTrendLabel(summary.mood_trend)}</span>
          </div>
        </div>

        <div className={expanded ? '' : 'line-clamp-3'}>
          <p className="text-gray-700 whitespace-pre-wrap">{summary.content}</p>
        </div>

        {summary.content.length > 300 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-primary-600 hover:underline mt-2"
          >
            {expanded ? 'Show less' : 'Read more'}
          </button>
        )}

        {summary.key_themes && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Key Themes</p>
            <div className="flex flex-wrap gap-2">
              {summary.key_themes.split(',').map((theme, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {theme.trim()}
                </span>
              ))}
            </div>
          </div>
        )}

        {summary.goal_progress && summary.goal_progress !== 'No specific goal updates' && (
          <div className="mt-4 pt-4 border-t">
            <p className="text-xs font-medium text-gray-500 uppercase mb-2">Goal Progress</p>
            <p className="text-sm text-gray-600">{summary.goal_progress}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function InsightsPage() {
  const [summaries, setSummaries] = useState<AutoSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<'weekly' | 'monthly' | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadSummaries();
  }, []);

  async function loadSummaries() {
    try {
      const data = await api.getSummaries();
      setSummaries(data.summaries);
    } catch (err) {
      console.error('Failed to load summaries:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate(type: 'weekly' | 'monthly') {
    setGenerating(type);
    setError(null);

    try {
      const response = type === 'weekly'
        ? await api.generateWeeklySummary()
        : await api.generateMonthlySummary();

      if (response.is_new) {
        setSummaries(prev => [response.summary, ...prev]);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate summary';
      setError(errorMessage);
    } finally {
      setGenerating(null);
    }
  }

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading insights...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Insights</h1>
          <p className="text-gray-500 mt-1">AI-generated reflections on your journaling journey</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleGenerate('weekly')}
            disabled={generating !== null}
          >
            {generating === 'weekly' ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 mr-2" />
            )}
            Weekly Summary
          </Button>
          <Button
            variant="outline"
            onClick={() => handleGenerate('monthly')}
            disabled={generating !== null}
          >
            {generating === 'monthly' ? (
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 mr-2" />
            )}
            Monthly Summary
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {summaries.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Sparkles className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No summaries yet</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Generate your first weekly or monthly summary to get AI-powered insights
              about your journaling patterns and emotional trends.
            </p>
            <div className="flex justify-center gap-3">
              <Button onClick={() => handleGenerate('weekly')} disabled={generating !== null}>
                Generate Weekly Summary
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {summaries.map((summary) => (
            <SummaryCard key={summary.id} summary={summary} />
          ))}
        </div>
      )}
    </div>
  );
}
