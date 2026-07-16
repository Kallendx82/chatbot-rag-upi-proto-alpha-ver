/**
 * Settings + ephemeral UI state stores.
 *
 * Settings persist to localStorage (top-k, temperature, language, theme, debug).
 * UI store is in-memory only (sidebar open, active panels, modals).
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Settings, SourceChunk } from "@/types";

// ---------------------------------------------------------------------------
// Settings store (persisted)
// ---------------------------------------------------------------------------
interface SettingsState extends Settings {
  set: <K extends keyof Settings>(key: K, value: Settings[K]) => void;
  reset: () => void;
}

export const DEFAULT_SETTINGS: Settings = {
  topK: 5,
  temperature: 0.2,
  language: "id",
  // llama3.1:8b-instruct-q4_K_M is the intended default. It answers in
  // ~20-30s once Ollama has it resident; only a cold load (first request
  // after Ollama/backend restart, or >30 min idle) takes ~85s. The backend
  // warms this model up in the background at startup and LLM_REQUEST_TIMEOUT
  // has a matching safety margin, so this should stay fast in practice.
  model: "llama3.1:8b-instruct-q4_K_M",
  theme: "system",
  debugMode: false,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULT_SETTINGS,
      set: (key, value) => set({ [key]: value } as Partial<SettingsState>),
      reset: () => set({ ...DEFAULT_SETTINGS }),
    }),
    {
      name: "upi-rag-settings",
      version: 0.3,
      // v0.1 -> v0.2 temporarily switched the model default to qwen2.5:3b;
      // v0.3 reverts to llama3.1:8b-instruct-q4_K_M (the intended default,
      // now that the backend warms it up + has a longer timeout instead of
      // needing a faster model). Force this for anyone below v0.3 without
      // touching their other saved preferences.
      migrate: (persisted, version) => {
        const state = persisted as Settings;
        if (version < 0.3) {
          return { ...state, model: DEFAULT_SETTINGS.model };
        }
        return state;
      },
    },
  ),
);

// ---------------------------------------------------------------------------
// UI store (ephemeral)
// ---------------------------------------------------------------------------
interface UIState {
  sidebarOpen: boolean;
  settingsOpen: boolean;
  /** Auth dialog (login/daftar) — deliberately separate from Settings. */
  authModalOpen: boolean;
  /** The source chunk currently expanded in the citation drawer, if any. */
  inspectedSource: SourceChunk | null;
  /** Whether the retrieval debug panel is open. */
  debugPanelOpen: boolean;

  toggleSidebar: () => void;
  setSidebar: (open: boolean) => void;
  setSettingsOpen: (open: boolean) => void;
  setAuthModalOpen: (open: boolean) => void;
  inspectSource: (s: SourceChunk | null) => void;
  setDebugPanelOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: false,
  settingsOpen: false,
  authModalOpen: false,
  inspectedSource: null,
  debugPanelOpen: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebar: (open) => set({ sidebarOpen: open }),
  setSettingsOpen: (open) => set({ settingsOpen: open }),
  setAuthModalOpen: (open) => set({ authModalOpen: open }),
  inspectSource: (s) => set({ inspectedSource: s }),
  setDebugPanelOpen: (open) => set({ debugPanelOpen: open }),
}));
