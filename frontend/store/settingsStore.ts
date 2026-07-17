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
  // Deliberate default, not just a fallback: with Ollama assigned to the
  // RTX 4050 (NVIDIA Control Panel -> High performance), qwen2.5:3b runs
  // 100% GPU at 2.1 GB VRAM (~14s per RAG-grounded answer), while
  // llama3.1:8b-instruct-q4_K_M only reaches 78% GPU at 5.3 GB (~56s) and,
  // staying resident for its 30 min keep_alive, left just ~0.6 GB of this
  // 6 GB card free - enough to visibly corrupt rendering in other
  // GPU-accelerated apps (observed in Claude Code) while it sat loaded.
  // llama3.1:8b-instruct-q4_K_M is still selectable per-request from
  // Settings for when accuracy matters more than multitasking safety.
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
      version: 0.4,
      // v0.1 -> v0.2: default -> qwen2.5:3b. v0.2 -> v0.3: default ->
      // llama3.1:8b-instruct-q4_K_M (assumed fixed by backend warm-up).
      // v0.3 -> v0.4: back to qwen2.5:3b for good - see the comment on
      // DEFAULT_SETTINGS.model above. Force the current default for anyone
      // below v0.4 without touching their other saved preferences.
      migrate: (persisted, version) => {
        const state = persisted as Settings;
        if (version < 0.4) {
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
