export interface User {
  id: string;
  email: string;
  name: string;
  total_xp?: number;
  level?: number;
  created_at: string;
}

export type JournalType = 'morning' | 'evening' | 'freeform';

export interface JournalEntry {
  id: string;
  title?: string;
  content: string;
  transcript?: string;
  mood?: 'great' | 'good' | 'okay' | 'bad' | 'terrible';
  journal_type?: JournalType;
  created_at: string;
  updated_at: string;
}

export type JournalingSchedule = 'morning' | 'evening' | 'both';

export interface Goal {
  id: string;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  progress: number;
  target_date?: string;
  journaling_schedule?: JournalingSchedule;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  entry_id?: string;
  session_type?: string;
  summary?: string;
  key_topics?: string;
  goal_updates?: string;
  created_at: string;
  messages: ChatMessage[];
}

export interface VoiceSession {
  id: string;
  session_type: string;
  summary?: string;
  key_topics?: string;
  goal_updates?: string;
  created_at: string;
  message_count: number;
}

export interface Metrics {
  total_entries: number;
  current_streak: number;
  longest_streak: number;
  entries_this_week: number;
  entries_this_month: number;
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  total_xp: number;
  level: number;
  morning_completed_today: boolean;
  evening_completed_today: boolean;
}

export interface Achievement {
  key: string;
  name: string;
  description: string;
  icon: string;
  unlocked_at?: string;
  progress?: number;
  target?: number;
}

export interface XPEvent {
  event_type: string;
  xp_amount: number;
  created_at: string;
}

export interface GamificationStats {
  total_xp: number;
  level: number;
  xp_for_next_level: number;
  xp_progress_in_level: number;
  current_streak: number;
  longest_streak: number;
  achievements: Achievement[];
  recent_xp_events: XPEvent[];
}

export interface ScheduleStatus {
  morning_completed: boolean;
  evening_completed: boolean;
  morning_prompt?: string;
  evening_prompt?: string;
  should_show_morning: boolean;
  should_show_evening: boolean;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface EntryListResponse {
  entries: JournalEntry[];
  total: number;
  page: number;
  limit: number;
}
