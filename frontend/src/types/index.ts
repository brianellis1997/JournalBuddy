export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface JournalEntry {
  id: string;
  title?: string;
  content: string;
  mood?: 'great' | 'good' | 'okay' | 'bad' | 'terrible';
  created_at: string;
  updated_at: string;
}

export interface Goal {
  id: string;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'paused' | 'abandoned';
  target_date?: string;
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
  created_at: string;
  messages: ChatMessage[];
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
