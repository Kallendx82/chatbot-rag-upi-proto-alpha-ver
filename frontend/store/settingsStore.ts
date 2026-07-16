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
  // qwen2.5:3b is the tuned default (fast, ~10-30s replies); llama3.1:8b
  // routinely exceeds LLM_REQUEST_TIMEOUT on this hardware and falls back
  // to a generic "server busy" error instead of answering.
  model: "qwen2.5:3b",
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
      version: 0.2,
      // v0.1 persisted llama3.1:8b as the model default; force existing
      // browsers onto the faster tuned default without touching their
      // other saved preferences (topK, temperature, theme, language).
      migrate: (persisted, version) => {
        const state = persisted as Settings;
        if (version < 0.2) {
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
