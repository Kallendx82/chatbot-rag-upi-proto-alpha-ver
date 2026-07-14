/**
 * useChat - orchestrates sending a message and rendering the response.
 *
 * STREAMING-CAPABLE ARCHITECTURE:
 * The backend has no SSE endpoint yet (deferred to a later slice). To make the
 * UI feel like a streaming chat today AND make the future swap trivial, this
 * hook treats answer rendering as a stream of deltas:
 *
 *   1. add user message + assistant placeholder (status "streaming")
 *   2. await the /api/chat response (full answer + sources + metrics)
 *   3. animate the answer into the placeholder token-by-token via appendToMessage
 *   4. finalize with sources + metrics (status "complete")
 *
 * The core answer step is factored into `generate()` so BOTH the first send and
 * a retry/regenerate reuse it. Crucially, `retry()` does NOT add a new user
 * message — it reuses the existing one — so retrying never duplicates the
 * question. `generate()` also auto-retries transient failures (Ollama busy /
 * brief 5xx) a few times before surfacing a friendly, localized error, so a
 * momentary HTTP 500 recovers silently instead of flashing an error.
 */
"use client";

import { useCallback, useRef, useState } from "react";

import { api, fetchChat } from "@/services/api";
import { useConversationStore } from "@/store/conversationStore";
import { useSettingsStore } from "@/store/settingsStore";
import { ApiError, type ChatMessage, type Language } from "@/types";

/** Animate text into the store as if streamed. Resolves when fully written. */
async function animateInto(
  text: string,
  onDelta: (delta: string) => void,
  signal: AbortSignal,
) {
  // Chunk by words for a natural cadence; keep it quick for long answers.
  const tokens = text.match(/\S+\s*/g) ?? [text];
  const perTick = tokens.length > 120 ? 3 : 1;
  for (let i = 0; i < tokens.length; i += perTick) {
    if (signal.aborted) return;
    onDelta(tokens.slice(i, i + perTick).join(""));
    // ~14ms/word feels responsive without being instant.
    await new Promise((r) => setTimeout(r, 14 * perTick));
  }
}

/** Status codes worth auto-retrying: network down, timeout, server busy. */
const TRANSIENT_STATUS = new Set([404, 408, 500, 502, 503, 504]);

/** Map a failure to a friendly, localized message (never a raw "HTTP 500"). */
function friendlyError(err: unknown, language: Language): string {
  const status = err instanceof ApiError ? err.status : -1;
  const id = {
    busy: "Server sedang sibuk memproses permintaan. Silakan coba lagi sebentar lagi.",
    net: "Tidak dapat terhubung ke server. Pastikan layanan backend sedang berjalan.",
    timeout: "Server membutuhkan waktu lebih lama dari biasanya. Silakan coba lagi.",
    generic: "Terjadi kesalahan saat memproses permintaan. Silakan coba lagi.",
  };
  const en = {
    busy: "The server is busy processing your request. Please try again in a moment.",
    net: "Cannot reach the server. Make sure the backend service is running.",
    timeout: "The server took longer than usual. Please try again.",
    generic: "Something went wrong while processing your request. Please try again.",
  };
  const t = language === "en" ? en : id;
  if (status === 404) return t.net;
  if (status === 408) return t.timeout;
  if (status >= 500) return t.busy;
  return t.generic;
}

export function useChat() {
  const [isSending, setIsSending] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const activeTurnRef = useRef<{ convId: string; assistantId: string } | null>(
    null,
  );

  const {
    getActive,
    newConversation,
    addUserMessage,
    addAssistantPlaceholder,
    appendToMessage,
    finalizeAssistantMessage,
    setMessageSources,
    setMessageError,
    removeMessage,
  } = useConversationStore();

  /**
   * Produce an assistant answer for `userText` in `convId`. Adds ONLY the
   * assistant placeholder (the user message must already exist). Auto-retries
   * transient errors before giving up with a friendly message.
   */
  const generate = useCallback(
    async (convId: string, userText: string) => {
      setIsSending(true);
      const abort = new AbortController();
      abortRef.current = abort;

      const assistantId = addAssistantPlaceholder(convId);
      activeTurnRef.current = { convId, assistantId };
      const { topK, temperature, language, model } = useSettingsStore.getState();

      const MAX_TRIES = 3;
      let lastErr: unknown = null;

      for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
        if (abort.signal.aborted) break;
        try {
          if (attempt === 1) {
            try {
              const retrieval = await api.retrieve({
                query: userText,
                top_k: topK,
              }, abort.signal);
              setMessageSources(convId, assistantId, retrieval.results);
            } catch {
              // Retrieval is also performed by /api/chat. This preflight call
              // only drives the loading phase label, so a failure here should
              // not block the actual answer generation.
            }
          }

          const res = await fetchChat({
            message: userText,
            top_k: topK,
            temperature,
            language,
            model,
          }, abort.signal);

          // Render progressively, then finalize with the canonical content.
          await animateInto(
            res.answer,
            (delta) => appendToMessage(convId, assistantId, delta),
            abort.signal,
          );

          finalizeAssistantMessage(convId, assistantId, {
            content: res.answer,
            sources: res.sources,
            metrics: {
              backend: res.backend,
              grounded: res.grounded,
              retrievalMs: res.retrieval_latency_ms,
              generationMs: res.generation_latency_ms,
              totalMs: res.total_latency_ms,
            },
          });
          setIsSending(false);
          abortRef.current = null;
          activeTurnRef.current = null;
          return; // success
        } catch (err) {
          lastErr = err;
          const status = err instanceof ApiError ? err.status : -1;
          if (status === -2 || abort.signal.aborted) {
            // User-initiated Stop: keep the turn (as an error state) instead
            // of deleting it, so edit/retry/copy stay available under the
            // user bubble — matches every other failure mode.
            setMessageError(convId, assistantId, "__stopped__");
            setIsSending(false);
            abortRef.current = null;
            activeTurnRef.current = null;
            return;
          }
          const transient = TRANSIENT_STATUS.has(status);
          // Stop retrying on non-transient errors, the last attempt, or abort.
          if (!transient || attempt === MAX_TRIES || abort.signal.aborted) break;
          // Brief backoff. Content stays empty, so the loading indicator keeps
          // showing — the user never sees the transient failure.
          await new Promise((r) => setTimeout(r, 1200 * attempt));
        }
      }

      setMessageError(convId, assistantId, friendlyError(lastErr, language));
      setIsSending(false);
      abortRef.current = null;
      activeTurnRef.current = null;
    },
    [
      addAssistantPlaceholder,
      appendToMessage,
      finalizeAssistantMessage,
      setMessageSources,
      setMessageError,
    ],
  );

  const send = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      if (!text || isSending) return;

      // Ensure there is an active conversation.
      let convId = getActive()?.id;
      if (!convId) convId = newConversation();

      addUserMessage(convId, text);
      await generate(convId, text);
    },
    [isSending, getActive, newConversation, addUserMessage, generate],
  );

  /**
   * Stop an in-flight turn. Aborting here lets generate()'s own catch block
   * mark the assistant message as "__stopped__" (rather than deleting it),
   * so the user bubble keeps its edit/retry/copy actions instead of the
   * question silently losing its answer.
   */
  const stop = useCallback(() => {
    abortRef.current?.abort();
    activeTurnRef.current = null;
    setIsSending(false);
  }, []);

  /**
   * Retry / regenerate: drop ONLY the target assistant message and re-answer
   * the SAME preceding user message. Does not add a new user message, so the
   * question is never duplicated (works for both a failed answer and the
   * "Hasilkan ulang" action on a finished answer).
   */
  const retry = useCallback(
    async (target: ChatMessage) => {
      const conv = getActive();
      if (!conv) return;
      const idx = conv.messages.findIndex((m) => m.id === target.id);
      if (idx < 1) return;
      const prevUser = conv.messages[idx - 1];
      if (prevUser?.role !== "user") return;
      // Pin the active id so generate() stays in this conversation.
      useConversationStore.getState().setActive(conv.id);
      removeMessage(conv.id, target.id);
      await generate(conv.id, prevUser.content);
    },
    [getActive, removeMessage, generate],
  );

  /**
   * Edit a user message in place (no new bubble) and regenerate its answer.
   * Drops the stale assistant reply, if any, before re-asking.
   */
  const editAndRetry = useCallback(
    async (userMessage: ChatMessage, newText: string) => {
      const text = newText.trim();
      if (!text) return;
      const conv = getActive();
      if (!conv) return;
      const idx = conv.messages.findIndex((m) => m.id === userMessage.id);
      if (idx === -1) return;
      const next = conv.messages[idx + 1];
      useConversationStore.getState().editUserMessage(conv.id, userMessage.id, text);
      if (next?.role === "assistant") {
        removeMessage(conv.id, next.id);
      }
      useConversationStore.getState().setActive(conv.id);
      await generate(conv.id, text);
    },
    [getActive, removeMessage, generate],
  );

  const deleteAndFollowing = useCallback(
    (target: ChatMessage) => {
      const conv = getActive();
      if (!conv) return;
      const idx = conv.messages.findIndex((m) => m.id === target.id);
      if (idx === -1) return;
      const idsToDelete = conv.messages.slice(idx).map((m) => m.id);
      const count = idsToDelete.length;
      const language = useSettingsStore.getState().language;
      const msg = language === "en"
        ? `Delete this message and ${count - 1} following message(s)?`
        : `Hapus pesan ini dan ${count - 1} pesan berikutnya?`;
      if (!window.confirm(msg)) return;
      for (const msgId of idsToDelete) {
        removeMessage(conv.id, msgId);
      }
      const notif = language === "en"
        ? `Deleted ${count} message(s)`
        : `${count} pesan dihapus`;
      alert(notif);
    },
    [getActive, removeMessage],
  );

  return { send, stop, retry, editAndRetry, deleteAndFollowing, isSending };
}
