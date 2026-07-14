"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Check,
  Copy,
  Pencil,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Timer,
  Trash2,
  User,
  X,
} from "lucide-react";

import { BrandLogo } from "@/components/ui/BrandLogo";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MarkdownMessage } from "@/components/chat/MarkdownMessage";
import { SourceList } from "@/components/citations/SourceInspector";
import { useSettingsStore } from "@/store/settingsStore";
import type { ChatMessage } from "@/types";
import { cn } from "@/lib/utils";

/**
 * Stored error text for a broken turn is either a free-form message (already
 * localized at the time it happened) or one of two stable markers set by
 * code that doesn't know the user's current language preference — a Stop
 * click, or rehydrating a turn orphaned by an abrupt session end. Markers are
 * translated here, at render time, using the CURRENT language setting.
 */
function errorText(error: string | undefined, language: "id" | "en"): string {
  if (error === "__stopped__") {
    return language === "en"
      ? "Stopped by you before finishing."
      : "Dihentikan oleh Anda sebelum selesai.";
  }
  if (error === "__interrupted__") {
    return language === "en"
      ? "The session ended before this question was answered."
      : "Sesi berakhir sebelum pertanyaan ini sempat dijawab.";
  }
  return (
    error ||
    (language === "en" ? "Failed to load the answer." : "Gagal memuat jawaban.")
  );
}

export function MessageBubble({
  message,
  nextMessage,
  onRetry,
  onEditRetry,
  onDelete,
}: {
  message: ChatMessage;
  /** The message immediately after this one, used to detect a broken answer
   * when rendering the user bubble's own edit/retry/copy actions. */
  nextMessage?: ChatMessage;
  onRetry?: (m: ChatMessage) => void;
  onEditRetry?: (userMessage: ChatMessage, newText: string) => void;
  onDelete?: (m: ChatMessage) => void;
}) {
  const isUser = message.role === "user";
  const debugMode = useSettingsStore((s) => s.debugMode);
  const language = useSettingsStore((s) => s.language);
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(message.content);
  const editRef = useRef<HTMLTextAreaElement>(null);

  const brokenAnswer =
    isUser && nextMessage?.role === "assistant" && nextMessage.status === "error";

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  const startEdit = () => {
    setDraft(message.content);
    setEditing(true);
    requestAnimationFrame(() => editRef.current?.focus());
  };

  const submitEdit = () => {
    const text = draft.trim();
    setEditing(false);
    if (text && text !== message.content) {
      onEditRetry?.(message, text);
    }
  };

  if (isUser && editing) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="flex flex-row-reverse gap-3"
      >
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <User className="h-4 w-4" />
        </div>
        <div className="flex min-w-0 max-w-[min(46rem,85%)] flex-1 flex-col items-end gap-2">
          <Textarea
            ref={editRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submitEdit();
              } else if (e.key === "Escape") {
                setEditing(false);
              }
            }}
            className="w-full resize-none text-[15px] leading-7"
            rows={Math.min(8, Math.max(2, draft.split("\n").length))}
          />
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
              <X className="h-3.5 w-3.5" />
              {language === "en" ? "Cancel" : "Batal"}
            </Button>
            <Button size="sm" onClick={submitEdit} disabled={!draft.trim()}>
              <RefreshCw className="h-3.5 w-3.5" />
              {language === "en" ? "Save & resend" : "Simpan & kirim ulang"}
            </Button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}
    >
      {/* Avatar */}
      <div
        className={cn(
          "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-accent/15 text-accent-foreground",
        )}
      >
        {isUser ? (
          <User className="h-4 w-4" />
        ) : (
          <BrandLogo className="h-6 w-6" iconClassName="h-4 w-4" />
        )}
      </div>

      {/* Body */}
      <div className={cn("min-w-0 max-w-[min(46rem,85%)]", isUser && "flex flex-col items-end")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-primary text-primary-foreground"
              : "border border-border bg-surface",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-[15px] leading-7">
              {message.content}
            </p>
          ) : message.status === "error" ? (
            <div className="flex items-start gap-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{errorText(message.error, language)}</span>
            </div>
          ) : message.status === "streaming" && !message.content ? (
            <TypingDots documentsFound={Boolean(message.sources?.length)} />
          ) : (
            <>
              <MarkdownMessage content={message.content} />
              {message.status === "streaming" && (
                <span className="ml-0.5 inline-block h-4 w-[2px] animate-blink bg-primary align-middle" />
              )}
            </>
          )}
        </div>

        {/* Assistant: grounding badge + metrics + actions + sources */}
        {!isUser && message.status === "complete" && (
          <div className="mt-2 w-full">
            <div className="flex flex-wrap items-center gap-2">
              {message.metrics && (
                <>
                  {message.metrics.grounded ? (
                    <Badge variant="teal" className="gap-1">
                      <ShieldCheck className="h-3 w-3" />
                      Terverifikasi sumber
                    </Badge>
                  ) : (
                    <Badge variant="muted" className="gap-1">
                      <ShieldAlert className="h-3 w-3" />
                      Tanpa sumber
                    </Badge>
                  )}
                  {debugMode && (
                    <Badge variant="outline" className="gap-1 font-mono">
                      <Timer className="h-3 w-3" />
                      {Math.round(message.metrics.totalMs)}ms
                    </Badge>
                  )}
                  {debugMode && (
                    <Badge variant="outline" className="font-mono">
                      {message.metrics.backend}
                    </Badge>
                  )}
                </>
              )}

              <div className="ml-auto flex items-center gap-1">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => copy(message.content)}
                    >
                      {copied ? (
                        <Check className="h-3.5 w-3.5" />
                      ) : (
                        <Copy className="h-3.5 w-3.5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Salin jawaban</TooltipContent>
                </Tooltip>
                {onRetry && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => onRetry(message)}
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Hasilkan ulang</TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>

            {message.sources && <SourceList sources={message.sources} />}
          </div>
        )}

        {/* User bubble: edit / retry / copy for a turn whose answer failed,
            was stopped, or was orphaned by an abrupt session end. Placed
            under the QUESTION rather than the broken answer, since the
            question is what the user acts on next. */}
        {isUser && brokenAnswer && (
          <div className="mt-1.5 flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon-sm" onClick={startEdit}>
                  <Pencil className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {language === "en" ? "Edit question" : "Edit pertanyaan"}
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onRetry?.(nextMessage!)}
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {language === "en" ? "Resend" : "Kirim ulang"}
              </TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => copy(message.content)}
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {language === "en" ? "Copy question" : "Salin pertanyaan"}
              </TooltipContent>
            </Tooltip>
            {onDelete && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => onDelete(message)}
                  >
                    <Trash2 className="h-3.5 w-3.5 text-destructive" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {language === "en" ? "Delete message" : "Hapus pesan"}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function TypingDots({ documentsFound }: { documentsFound: boolean }) {
  // Live elapsed-time counter + a phase label that progresses over time, so the
  // user sees what the system is doing. The thinking phase starts when the
  // retrieval preflight has found sources, not after a fixed timeout.
  const language = useSettingsStore((s) => s.language);
  const start = useRef(Date.now());
  const [secs, setSecs] = useState(0);
  useEffect(() => {
    const t = setInterval(
      () => setSecs((Date.now() - start.current) / 1000),
      200,
    );
    return () => clearInterval(t);
  }, []);

  const phase = documentsFound
    ? secs < 20
      ? language === "en"
        ? "Documents found, validating the contents..."
        : "Dokumen sudah ditemukan, sedang memvalidasi isi dokumen."
      : secs < 60
        ? language === "en"
          ? "Thinking..."
          : "Sedang berpikir..."
        : language === "en"
          ? "Still processing, please wait..."
          : "Masih memproses, mohon tunggu..."
    : secs < 30
      ? language === "en"
        ? "Searching for relevant documents..."
        : "Sedang mencari dokumen yang relevan..."
      : secs < 60
        ? language === "en"
          ? "Still searching for relevant documents..."
          : "Masih mencari dokumen yang relevan..."
        : language === "en"
          ? "Still processing, please wait..."
          : "Masih memproses, mohon tunggu...";

  const unit = language === "en" ? "s" : "dtk";

  return (
    <div className="flex items-center gap-2 py-1">
      <div className="flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-muted-foreground/60"
            style={{
              animation: "blink 1.2s ease-in-out infinite",
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
      <span className="text-xs text-muted-foreground">{phase}</span>
      <span className="font-mono text-xs tabular-nums text-muted-foreground/70">
        {secs.toFixed(1)} {unit}
      </span>
    </div>
  );
}
