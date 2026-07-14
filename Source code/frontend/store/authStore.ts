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
  lastUsername: string | null;
  /** True while login/register + initial sync is in flight. */
  busy: boolean;

  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  triggerPasswordSave: (username: string, password: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      lastUsername: null,
      busy: false,

      login: async (username, password) => {
        set({ busy: true });
        try {
          const res = await api.login(username, password);
          set({ token: res.token, user: res.user, lastUsername: username });
          get().triggerPasswordSave(username, password);
          await syncOnLogin(res.token);
        } finally {
          set({ busy: false });
        }
      },

      register: async (username, password) => {
        set({ busy: true });
        try {
          const res = await api.register(username, password);
          set({ token: res.token, user: res.user, lastUsername: username });
          get().triggerPasswordSave(username, password);
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

      triggerPasswordSave: (username: string, password: string) => {
        if (typeof window === "undefined" || !navigator.credentials) return;
        try {
          const PasswordCredential = (window as any).PasswordCredential;
          if (!PasswordCredential) return;
          const cred = new PasswordCredential({
            id: username,
            password: password,
            name: username,
          });
          void navigator.credentials.store(cred);
        } catch {
          // Browser doesn't support Credential Management API; that's fine.
        }
      },
    }),
    {
      name: "upi-rag-auth",
      version: 1,
      onRehydrateStorage: () => (state) => {
        // Saat app boot: jika ada lastUsername dan token, auto-login.
        if (state && state.lastUsername && state.token && state.user) {
          // State sudah ter-restore dari localStorage; tidak perlu berbuat apa-apa.
          // User sudah login dari session sebelumnya.
        }
      },
    },
  ),
);
