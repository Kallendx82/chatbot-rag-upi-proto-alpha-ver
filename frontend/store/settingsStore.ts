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
  // TEMPORARY default until Ollama is confirmed to be using the RTX 4050
  // instead of CPU (ollama ps showed "100% CPU", 0 B VRAM detected - a
  // classic Optimus laptop issue where the dGPU stays asleep unless an app
  // is explicitly assigned to it in the NVIDIA Control Panel). On CPU, a
  // real RAG request with llama3.1:8b-instruct-q4_K_M took >120s and still
  // fell back to extractive; qwen2.5:3b stays fast even on CPU. Switch back
  // to "llama3.1:8b-instruct-q4_K_M" (bump the persist version below too)
  // once the GPU fix is verified.
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
      // v0.3 -> v0.4: back to qwen2.5:3b - real testing showed Ollama was
      // running the 8B model on CPU (GPU not detected), where even a warm
      // request took >120s. Revisit once the GPU routing fix is confirmed.
      // Force the current default for anyone below v0.4 without touching
      // their other saved preferences.
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
