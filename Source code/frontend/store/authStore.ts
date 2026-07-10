/**
 * Auth store (Zustand + persist).
 *
 * Holds the bearer token + logged-in user. Persisted to localStorage so a
 * reload keeps you logged in (token itself expires server-side after 30 days).
 * Login/register also trigger a session sync: local conversations are pushed
 * to the account, then the server's list is pulled back (see sessionSync.ts).
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { api } from "@/services/api";
import { syncOnLogin } from "@/services/sessionSync";
import type { AuthUser } from "@/types";

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  /** True while login/register + initial sync is in flight. */
  busy: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      busy: false,

      login: async (username, password) => {
        set({ busy: true });
        try {
          const res = await api.login(username, password);
          set({ token: res.token, user: res.user });
          await syncOnLogin(res.token);
        } finally {
          set({ busy: false });
        }
      },

      register: async (username, password) => {
        set({ busy: true });
        try {
          const res = await api.register(username, password);
          set({ token: res.token, user: res.user });
          await syncOnLogin(res.token);
        } finally {
          set({ busy: false });
        }
      },

      logout: async () => {
        const token = get().token;
        set({ token: null, user: null });
        if (token) {
          try {
            await api.logout(token);
          } catch {
            // Token dihapus lokal; kegagalan revoke server tidak menghalangi.
          }
        }
      },
    }),
    { name: "upi-rag-auth", version: 1 },
  ),
);
