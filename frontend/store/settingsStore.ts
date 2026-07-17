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
  // Intended default (product decision): llama3.1:8b-instruct-q4_K_M for
  // accuracy - qwen2.5:3b was kept only as a speed/VRAM comparison
  // baseline during GPU-offload testing, not meant to ship as default.
  // Trade-offs to be aware of on a 6 GB VRAM card (RTX 4050): ~56s per
  // answer at 75% GPU / 5.6 GB VRAM (num_ctx=4096), leaving only ~0.3 GB
  // free - tight enough to affect other GPU-accelerated apps while the
  // model is resident (30 min keep_alive after each use). qwen2.5:3b
  // remains selectable per-request from Settings when speed/multitasking
  // matters more than accuracy.
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
      version: 0.5,
      // v0.1 -> v0.2: default -> qwen2.5:3b. v0.2 -> v0.3: default ->
      // llama3.1:8b-instruct-q4_K_M. v0.3 -> v0.4: back to qwen2.5:3b
      // (GPU-offload testing baseline). v0.4 -> v0.5: llama3.1:8b-instruct
      // for good - see the comment on DEFAULT_SETTINGS.model above. Force
      // the current default for anyone below v0.5 without touching their
      // other saved preferences.
      migrate: (persisted, version) => {
        const state = persisted as Settings;
        if (version < 0.5) {
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
