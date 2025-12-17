'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Card, CardContent } from '@/components/ui/Card';
import { Modal } from '@/components/ui/Modal';
import { cn } from '@/lib/utils';
import type { Goal } from '@/types';

const statusOptions = [
  { value: 'active', label: 'Active', color: 'bg-green-100 text-green-700' },
  { value: 'completed', label: 'Completed', color: 'bg-blue-100 text-blue-700' },
  { value: 'paused', label: 'Paused', color: 'bg-yellow-100 text-yellow-700' },
  { value: 'abandoned', label: 'Abandoned', color: 'bg-gray-100 text-gray-700' },
];

export default function GoalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [goal, setGoal] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    status: '',
    target_date: '',
  });

  useEffect(() => {
    loadGoal();
  }, [params.id]);

  async function loadGoal() {
    try {
      const data = await api.getGoal(params.id as string);
      setGoal(data);
      setEditForm({
        title: data.title,
        description: data.description || '',
        status: data.status,
        target_date: data.target_date || '',
      });
    } catch (error) {
      console.error('Failed to load goal:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!editForm.title.trim()) return;
    setSaving(true);
    try {
      await api.updateGoal(params.id as string, {
        title: editForm.title.trim(),
        description: editForm.description.trim() || undefined,
        status: editForm.status,
        target_date: editForm.target_date || undefined,
      });
      router.push('/goals');
    } catch (error) {
      console.error('Failed to update goal:', error);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    try {
      await api.deleteGoal(params.id as string);
      router.push('/goals');
    } catch (error) {
      console.error('Failed to delete goal:', error);
    }
  }

  if (loading) {
    return <div className="animate-pulse text-gray-500">Loading goal...</div>;
  }

  if (!goal) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Goal not found.</p>
        <Link href="/goals" className="text-primary-600 hover:underline mt-2 inline-block">
          Back to Goals
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/goals">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <Button variant="danger" size="sm" onClick={() => setShowDeleteModal(true)}>
          <Trash2 className="w-4 h-4 mr-2" />
          Delete
        </Button>
      </div>

      <Card>
        <CardContent className="py-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Goal Title
            </label>
            <Input
              type="text"
              value={editForm.title}
              onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <Textarea
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              rows={4}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex gap-2 flex-wrap">
              {statusOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setEditForm({ ...editForm, status: option.value })}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors border-2',
                    editForm.status === option.value
                      ? `${option.color} border-current`
                      : 'bg-gray-50 text-gray-600 border-transparent hover:bg-gray-100'
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Date
            </label>
            <Input
              type="date"
              value={editForm.target_date}
              onChange={(e) => setEditForm({ ...editForm, target_date: e.target.value })}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Link href="/goals">
              <Button variant="outline">Cancel</Button>
            </Link>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Goal"
      >
        <p className="text-gray-600 mb-6">
          Are you sure you want to delete this goal? This action cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  );
}
