'use client';

import { useEffect, useState } from 'react';
import { Trophy, Star, Flame, TrendingUp } from 'lucide-react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader } from '@/components/ui/Card';
import { XPProgressBar } from '@/components/gamification/XPProgressBar';
import { LevelBadge } from '@/components/gamification/LevelBadge';
import { StreakDisplay } from '@/components/gamification/StreakDisplay';
import { AchievementCard } from '@/components/gamification/AchievementCard';
import type { Achievement, GamificationStats, XPEvent } from '@/types';

export default function ProgressPage() {
  const [stats, setStats] = useState<GamificationStats | null>(null);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [xpHistory, setXPHistory] = useState<XPEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, achievementsData, xpHistoryData] = await Promise.all([
          api.getGamificationStats(),
          api.getAchievements(),
          api.getXPHistory(10),
        ]);
        setStats(statsData);
        setAchievements(achievementsData);
        setXPHistory(xpHistoryData);
      } catch (error) {
        console.error('Failed to load progress data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading progress...</div>;
  }

  const unlockedAchievements = achievements.filter((a) => a.unlocked_at);
  const lockedAchievements = achievements.filter((a) => !a.unlocked_at);

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <Trophy className="w-8 h-8 text-purple-600" />
        <h1 className="text-2xl font-bold text-gray-900">Your Progress</h1>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="py-6">
              <div className="flex items-center gap-4">
                <LevelBadge level={stats.level} size="lg" />
                <div>
                  <p className="text-lg font-semibold text-gray-900">Level {stats.level}</p>
                  <p className="text-sm text-gray-500">{stats.total_xp} XP total</p>
                </div>
              </div>
              <div className="mt-4">
                <XPProgressBar
                  currentXP={stats.total_xp}
                  level={stats.level}
                  xpForNextLevel={stats.xp_for_next_level}
                  xpForCurrentLevel={stats.xp_for_current_level}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-orange-100 rounded-lg">
                  <Flame className="w-8 h-8 text-orange-600" />
                </div>
                <StreakDisplay
                  currentStreak={stats.current_streak}
                  longestStreak={stats.longest_streak}
                  size="lg"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Star className="w-8 h-8 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{unlockedAchievements.length}</p>
                  <p className="text-sm text-gray-500">
                    of {achievements.length} achievements
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {unlockedAchievements.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  Unlocked Achievements
                </h2>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {unlockedAchievements.map((achievement) => (
                  <AchievementCard
                    key={achievement.key}
                    achievement={achievement}
                    size="sm"
                  />
                ))}
              </CardContent>
            </Card>
          )}

          {lockedAchievements.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-gray-600">
                  Achievements to Unlock
                </h2>
              </CardHeader>
              <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {lockedAchievements.map((achievement) => (
                  <AchievementCard
                    key={achievement.key}
                    achievement={achievement}
                    size="sm"
                  />
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        <div>
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                Recent XP
              </h2>
            </CardHeader>
            <CardContent className="space-y-3">
              {xpHistory.length === 0 ? (
                <p className="text-gray-500 text-sm text-center py-4">
                  No XP earned yet. Start journaling!
                </p>
              ) : (
                xpHistory.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {formatEventType(event.event_type)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(event.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="text-sm font-bold text-green-600">
                      +{event.xp_amount} XP
                    </span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function formatEventType(eventType: string): string {
  const typeMap: Record<string, string> = {
    entry_created: 'Journal Entry',
    morning_journal: 'Morning Journal',
    evening_journal: 'Evening Journal',
    goal_created: 'Goal Created',
    goal_completed: 'Goal Completed',
    streak_7: '7-Day Streak Bonus',
    streak_30: '30-Day Streak Bonus',
  };
  return typeMap[eventType] || eventType.replace(/_/g, ' ');
}
