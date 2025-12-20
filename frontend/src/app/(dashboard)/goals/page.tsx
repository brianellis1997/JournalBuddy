'use client';

import { useEffect, useState } from 'react';
import { Plus, Check, Pause, X } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import type { Goal } from '@/types';
import { cn } from '@/lib/utils';

const statusTabs = [
  { value: undefined, label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'paused', label: 'Paused' },
];

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  completed: 'bg-blue-100 text-blue-700',
  paused: 'bg-yellow-100 text-yellow-700',
  abandoned: 'bg-gray-100 text-gray-700',
};

export default function GoalsPage() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [showNewModal, setShowNewModal] = useState(false);
  const [newGoal, setNewGoal] = useState({ title: '', description: '', target_date: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadGoals();
  }, [statusFilter]);

  async function loadGoals() {
    try {
      setLoading(true);
      const data = await api.getGoals(statusFilter);
      setGoals(data);
    } catch (error) {
      console.error('Failed to load goals:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateGoal(e: React.FormEvent) {
    e.preventDefault();
    if (!newGoal.title.trim()) return;

    setSaving(true);
    try {
      await api.createGoal({
        title: newGoal.title.trim(),
        description: newGoal.description.trim() || undefined,
        target_date: newGoal.target_date || undefined,
      });
      setShowNewModal(false);
      setNewGoal({ title: '', description: '', target_date: '' });
      loadGoals();
    } catch (error) {
      console.error('Failed to create goal:', error);
    } finally {
      setSaving(false);
    }
  }

  async function updateGoalStatus(goalId: string, status: string) {
    try {
      await api.updateGoal(goalId, { status });
      loadGoals();
    } catch (error) {
      console.error('Failed to update goal:', error);
    }
  }

  async function deleteGoal(goalId: string) {
    try {
      await api.deleteGoal(goalId);
      loadGoals();
    } catch (error) {
      console.error('Failed to delete goal:', error);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Goals</h1>
        <Button onClick={() => setShowNewModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Goal
        </Button>
      </div>

      <div className="flex gap-2">
        {statusTabs.map((tab) => (
          <button
            key={tab.label}
            onClick={() => setStatusFilter(tab.value)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              statusFilter === tab.value
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="animate-pulse text-gray-500">Loading goals...</div>
      ) : goals.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">
              {statusFilter ? `No ${statusFilter} goals.` : 'No goals yet. Set your first goal!'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {goals.map((goal) => (
            <Card key={goal.id}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="font-medium text-gray-900">{goal.title}</h3>
                      <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusColors[goal.status])}>
                        {goal.status}
                      </span>
                    </div>
                    {goal.description && (
                      <p className="text-sm text-gray-500 mt-1">{goal.description}</p>
                    )}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>Progress</span>
                        <span>{goal.progress}%</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            'h-full rounded-full transition-all duration-300',
                            goal.progress === 100 ? 'bg-green-500' : 'bg-primary-500'
                          )}
                          style={{ width: `${goal.progress}%` }}
                        />
                      </div>
                    </div>
                    {goal.target_date && (
                      <p className="text-xs text-gray-400 mt-2">
                        Target: {new Date(goal.target_date).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 ml-4">
                    {goal.status === 'active' && (
                      <>
                        <button
                          onClick={() => updateGoalStatus(goal.id, 'completed')}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                          title="Mark complete"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => updateGoalStatus(goal.id, 'paused')}
                          className="p-2 text-yellow-600 hover:bg-yellow-50 rounded-lg"
                          title="Pause"
                        >
                          <Pause className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    {goal.status === 'paused' && (
                      <button
                        onClick={() => updateGoalStatus(goal.id, 'active')}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                        title="Resume"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                    {goal.status === 'completed' && (
                      <button
                        onClick={() => updateGoalStatus(goal.id, 'active')}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                        title="Reopen"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => deleteGoal(goal.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={showNewModal}
        onClose={() => setShowNewModal(false)}
        title="New Goal"
      >
        <form onSubmit={handleCreateGoal} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Goal Title
            </label>
            <Input
              type="text"
              placeholder="What do you want to achieve?"
              value={newGoal.title}
              onChange={(e) => setNewGoal({ ...newGoal, title: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description (optional)
            </label>
            <Textarea
              placeholder="Add more details about your goal..."
              value={newGoal.description}
              onChange={(e) => setNewGoal({ ...newGoal, description: e.target.value })}
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Date (optional)
            </label>
            <Input
              type="date"
              value={newGoal.target_date}
              onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" type="button" onClick={() => setShowNewModal(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Creating...' : 'Create Goal'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
