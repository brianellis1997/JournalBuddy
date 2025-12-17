import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Token } from '@/types';
import { api } from '@/lib/api';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  setAuth: (user: User, tokens: Token) => void;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoading: true,

      setAuth: (user, tokens) => {
        api.setToken(tokens.access_token);
        set({
          user,
          token: tokens.access_token,
          refreshToken: tokens.refresh_token,
          isLoading: false,
        });
      },

      logout: () => {
        api.setToken(null);
        set({
          user: null,
          token: null,
          refreshToken: null,
          isLoading: false,
        });
      },

      loadUser: async () => {
        const { token } = get();
        if (!token) {
          set({ isLoading: false });
          return;
        }

        api.setToken(token);
        try {
          const user = await api.getCurrentUser();
          set({ user, isLoading: false });
        } catch {
          set({ user: null, token: null, refreshToken: null, isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
