"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/contexts/I18nContext";
import { cn } from "@/lib/utils";

/**
 * Chat composer.
 * - multiline, auto-growing textarea
 * - Enter sends; Shift+Enter inserts a newline
 * - shows a Stop button while a response is rendering
 * - disabled (with reason) when the backend is offline
 */
export function ChatInput({
  onSend,
  onStop,
  isSending,
  disabled,
  disabledReason,
}: {
  onSend: (text: string) => void;
  onStop: () => void;
  isSending: boolean;
  disabled?: boolean;
  disabledReason?: string;
}) {
  const { t } = useI18n();
  const DRAFT_KEY = "upi-rag-draft";
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const restoredRef = useRef(false);

  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    const saved = localStorage.getItem(DRAFT_KEY);
    if (saved) setValue(saved);
  }, []);

  useEffect(() => {
    if (!restoredRef.current) return;
    if (value) localStorage.setItem(DRAFT_KEY, value);
    else localStorage.removeItem(DRAFT_KEY);
  }, [value]);

  // Auto-grow up to a max height.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [value]);

  const submit = () => {
    const text = value.trim();
    if (!text || isSending || disabled) return;
    onSend(text);
    setValue("");
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-4">
      <div
        className={cn(
          "relative flex items-end gap-2 rounded-2xl border border-border bg-surface p-2 shadow-sm transition-colors focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring/40",
          disabled && "opacity-60",
        )}
      >
        <Textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            disabled
              ? disabledReason || t("common.appName")
              : t("welcome.placeholder")
          }
          className="max-h-[200px] flex-1 border-0 bg-transparent px-2 py-2 shadow-none focus-visible:ring-0"
        />
        {isSending ? (
          <Button
            size="icon"
            variant="outline"
            onClick={onStop}
            aria-label="Stop"
            className="shrink-0 rounded-xl"
          >
            <Square className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={submit}
            disabled={!value.trim() || disabled}
            aria-label={t("welcome.send")}
            className="shrink-0 rounded-xl"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        )}
      </div>
      <p className="mt-2 text-center text-xs text-muted-foreground">
        {t("welcome.footer")}
      </p>
    </div>
  );
}
