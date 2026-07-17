"use client";

import { useEffect, useState } from "react";
import { Monitor, Moon, RotateCcw, Save, Sun } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DEFAULT_SETTINGS,
  useSettingsStore,
  useUIStore,
} from "@/store/settingsStore";
import { useI18n } from "@/contexts/I18nContext";
import type { Language, Settings, ThemeMode } from "@/types";
import { cn } from "@/lib/utils";

const SETTING_KEYS: (keyof Settings)[] = [
  "topK",
  "temperature",
  "language",
  "model",
  "theme",
  "debugMode",
];

type DraftSettings = Settings & { uiLanguage: "en" | "id" };

function snapshot(s: Settings, uiLang: "en" | "id"): DraftSettings {
  return {
    topK: s.topK,
    temperature: s.temperature,
    language: s.language,
    model: s.model,
    theme: s.theme,
    debugMode: s.debugMode,
    uiLanguage: uiLang,
  };
}

// Strings localized in THIS batch (the full app i18n is delegated to Codex).
const TXT = {
  id: {
    save: "Simpan",
    reset: "Atur ulang",
    leaveTitle: "Pergi tanpa menyimpan?",
    leaveDesc:
      "Perubahan yang Anda buat belum disimpan dan akan dikembalikan ke keadaan sebelumnya.",
    stay: "Tetap di sini",
    leave: "Tinggalkan tanpa menyimpan",
  },
  en: {
    save: "Save",
    reset: "Reset",
    leaveTitle: "Leave without saving?",
    leaveDesc:
      "The changes you made have not been saved and will be reverted to the previous state.",
    stay: "Stay here",
    leave: "Leave without saving",
  },
};

export function SettingsModal() {
  const open = useUIStore((s) => s.settingsOpen);
  const setOpen = useUIStore((s) => s.setSettingsOpen);

  const store = useSettingsStore();
  const { language: uiLanguage, setLanguage: setUILanguage } = useI18n();
  // Use the UI language for the modal's own labels to reflect current interface language
  const t = TXT[uiLanguage === "en" ? "en" : "id"];

  // Draft = local working copy. Edits stay here until the user presses Save.
  const [draft, setDraft] = useState<DraftSettings>(() => snapshot(store, uiLanguage));
  const [confirmLeave, setConfirmLeave] = useState(false);

  // Re-seed the draft from committed settings each time the modal opens.
  useEffect(() => {
    if (open) {
      setDraft(snapshot(useSettingsStore.getState(), uiLanguage));
      setConfirmLeave(false);
    }
  }, [open, uiLanguage]);

  const dirty = SETTING_KEYS.some((k) => draft[k] !== store[k]) || draft.uiLanguage !== uiLanguage;

  const setField = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    setDraft((d) => ({ ...d, [key]: value }));

  const commit = () => {
    const languageChanged = draft.uiLanguage !== uiLanguage;

    SETTING_KEYS.forEach((k) => {
      if (draft[k] !== store[k]) {
        store.set(k, draft[k] as never);
      }
    });
    if (languageChanged) {
      setUILanguage(draft.uiLanguage);
      setOpen(false);
      window.location.reload();
    } else {
      setOpen(false);
    }
  };

  // Intercept close attempts (X / Esc / outside click): confirm if dirty.
  const handleOpenChange = (next: boolean) => {
    if (next) {
      setOpen(true);
      return;
    }
    if (dirty) {
      setConfirmLeave(true);
      return;
    }
    setOpen(false);
  };

  const discardAndClose = () => {
    setConfirmLeave(false);
    setOpen(false);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Pengaturan</DialogTitle>
            <DialogDescription>
              Konfigurasi retrieval, model, tampilan, dan bahasa.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-5 py-1 max-h-96 overflow-y-auto">
            {/* Theme */}
            <div className="space-y-2">
              <Label>Tema</Label>
              <div className="grid grid-cols-3 gap-2">
                {(
                  [
                    { v: "light", icon: Sun, label: "Terang" },
                    { v: "dark", icon: Moon, label: "Gelap" },
                    { v: "system", icon: Monitor, label: "Sistem" },
                  ] as { v: ThemeMode; icon: typeof Sun; label: string }[]
                ).map(({ v, icon: Icon, label }) => (
                  <button
                    key={v}
                    onClick={() => setField("theme", v)}
                    className={cn(
                      "flex flex-col items-center gap-1.5 rounded-lg border p-3 text-xs transition-colors",
                      draft.theme === v
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border hover:bg-surface-muted",
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* UI Language */}
            <div className="space-y-2">
              <Label>{uiLanguage === "en" ? "Interface Language" : "Bahasa Antarmuka"}</Label>
              <Select
                value={draft.uiLanguage || "id"}
                onValueChange={(v) => setField("uiLanguage", v as "en" | "id")}
              >
                <SelectTrigger>
                  <SelectValue placeholder={draft.uiLanguage === "en" ? "English" : "Bahasa Indonesia"} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="id">Bahasa Indonesia</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Language */}
            <div className="space-y-2">
              <Label>Bahasa jawaban</Label>
              <Select
                value={draft.language}
                onValueChange={(v) => setField("language", v as Language)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="id">Bahasa Indonesia</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Top-k */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Top-K retrieval</Label>
                <span className="font-mono text-sm text-muted-foreground">
                  {draft.topK}
                </span>
              </div>
              <Slider
                min={1}
                max={20}
                step={1}
                value={[draft.topK]}
                onValueChange={([v]) => setField("topK", v)}
              />
              <p className="text-xs text-muted-foreground">
                Jumlah potongan dokumen yang diambil sebagai konteks.
              </p>
            </div>

            {/* Temperature */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Temperature</Label>
                <span className="font-mono text-sm text-muted-foreground">
                  {draft.temperature.toFixed(2)}
                </span>
              </div>
              <Slider
                min={0}
                max={1}
                step={0.05}
                value={[draft.temperature]}
                onValueChange={([v]) => setField("temperature", v)}
              />
              <p className="text-xs text-muted-foreground">
                (Disarankan ≤ 0.2).
              </p>
            </div>

            {/* Model label */}
            <div className="space-y-2">
              <Label>Backend model</Label>
              <Select
                value={draft.model}
                onValueChange={(v) => setField("model", v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="llama3.1:8b-instruct-q4_K_M">Llama 3.1 8B-Instruct</SelectItem>
                  <SelectItem value="llama3.1:8b">Llama 3.1 8B </SelectItem>
                  <SelectItem value="llama3.2:3b">Llama 3.2 3B</SelectItem>
                  <SelectItem value="qwen2.5:3b">Qwen 2.5:3B (default)</SelectItem>
                  <SelectItem value="qwen3.5:4b-q4_K_M">Qwen 3.5 4B-q4</SelectItem>
                  <SelectItem value="gemma4:e2b ">gemma4:e2b </SelectItem>

                  <SelectItem value="extractive">Extractive (tanpa LLM)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                Model lokal melalui Ollama. Qwen 2.5:3B (default) tetap
                cepat walau tanpa akselerasi GPU; Llama 3.1 8B lebih akurat
                tapi saat ini berjalan di CPU sehingga bisa sangat lambat
                (&gt;2 menit per jawaban).
              </p>
            </div>

            {/* Debug mode */}
            <div className="flex items-center justify-between rounded-lg border border-border p-3">
              <div>
                <Label>Mode debug</Label>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Tampilkan latensi & backend pada tiap jawaban.
                </p>
              </div>
              <Switch
                checked={draft.debugMode}
                onCheckedChange={(v) => setField("debugMode", v)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-border pt-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setDraft(snapshot(DEFAULT_SETTINGS, "id"))}
            >
              <RotateCcw className="h-3.5 w-3.5" />
              {t.reset}
            </Button>
            <Button size="sm" onClick={commit} disabled={!dirty}>
              <Save className="h-3.5 w-3.5" />
              {t.save}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Leave-without-saving confirmation */}
      <Dialog open={confirmLeave} onOpenChange={setConfirmLeave}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>{t.leaveTitle}</DialogTitle>
            <DialogDescription>{t.leaveDesc}</DialogDescription>
          </DialogHeader>
          <div className="mt-2 flex items-center justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setConfirmLeave(false)}
            >
              {t.stay}
            </Button>
            <Button variant="destructive" size="sm" onClick={discardAndClose}>
              {t.leave}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
