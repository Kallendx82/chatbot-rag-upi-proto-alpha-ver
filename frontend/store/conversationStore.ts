/**
 * Conversation store (Zustand + persist).
 *
 * Holds all conversations and the active id. Persisted to localStorage so chat
 * history survives reloads WITHOUT a backend (this slice's requirement). The
 * persistence layer is isolated here: when Slice 2 adds server-side history,
 * swap the `persist` storage for API-backed actions and nothing else in the UI
 * needs to change.
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { ChatMessage, Conversation, SourceChunk } from "@/types";
import { deriveTitle, uid } from "@/lib/utils";

/** Mirror a rename/delete to the server when a user is logged in. */
function mirrorToServer(fn: (token: string) => Promise<unknown>): void {
  void import("@/store/authStore").then(({ useAuthStore }) => {
    const token = useAuthStore.getState().token;
    if (token) fn(token).catch(() => {});
  });
}

interface ConversationState {
  conversations: Conversation[];
  activeId: string | null;

  // selectors-as-helpers
  getActive: () => Conversation | undefined;

  // mutations
  newConversation: () => string;
  deleteConversation: (id: string) => void;
  renameConversation: (id: string, title: string) => void;
  setActive: (id: string) => void;

  addUserMessage: (conversationId: string, content: string) => string;
  addAssistantPlaceholder: (conversationId: string) => string;
  appendToMessage: (
    conversationId: string,
    messageId: string,
    delta: string,
  ) => void;
  setMessageSources: (
    conversationId: string,
    messageId: string,
    sources: SourceChunk[],
  ) => void;
  finalizeAssistantMessage: (
    conversationId: string,
    messageId: string,
    payload: {
      content: string;
      sources: SourceChunk[];
      metrics: NonNullable<ChatMessage["metrics"]>;
    },
  ) => void;
  setMessageError: (
    conversationId: string,
    messageId: string,
    error: string,
  ) => void;
  editUserMessage: (
    conversationId: string,
    messageId: string,
    content: string,
  ) => void;
  removeMessage: (conversationId: string, messageId: string) => void;
}

function touch(conv: Conversation): Conversation {
  return { ...conv, updatedAt: Date.now() };
}

export const useConversationStore = create<ConversationState>()(
  persist(
    (set, get) => ({
      conversations: [],
      activeId: null,

      getActive: () => {
        const { conversations, activeId } = get();
        return conversations.find((c) => c.id === activeId);
      },

      newConversation: () => {
        const id = uid("conv_");
        const now = Date.now();
        const conv: Conversation = {
          id,
          title: "Percakapan baru",
          messages: [],
          createdAt: now,
          updatedAt: now,
        };
        set((s) => ({
          conversations: [conv, ...s.conversations],
          activeId: id,
        }));
        return id;
      },

      deleteConversation: (id) => {
        set((s) => {
          const remaining = s.conversations.filter((c) => c.id !== id);
          const activeId =
            s.activeId === id ? (remaining[0]?.id ?? null) : s.activeId;
          return { conversations: remaining, activeId };
        });
        mirrorToServer((token) =>
          import("@/services/api").then(({ api }) =>
            api.deleteSession(token, id),
          ),
        );
      },

      renameConversation: (id, title) => {
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === id ? touch({ ...c, title: title.trim() || c.title }) : c,
          ),
        }));
        const finalTitle = title.trim();
        if (finalTitle) {
          mirrorToServer((token) =>
            import("@/services/api").then(({ api }) =>
              api.renameSession(token, id, finalTitle),
            ),
          );
        }
      },

      setActive: (id) => set({ activeId: id }),

      addUserMessage: (conversationId, content) => {
        const msgId = uid("msg_");
        const msg: ChatMessage = {
          id: msgId,
          role: "user",
          content,
          createdAt: Date.now(),
          status: "complete",
        };
        set((s) => ({
          conversations: s.conversations.map((c) => {
            if (c.id !== conversationId) return c;
            const isFirst = c.messages.length === 0;
            return touch({
              ...c,
              title: isFirst ? deriveTitle(content) : c.title,
              messages: [...c.messages, msg],
            });
          }),
        }));
        return msgId;
      },

      addAssistantPlaceholder: (conversationId) => {
        const msgId = uid("msg_");
        const msg: ChatMessage = {
          id: msgId,
          role: "assistant",
          content: "",
          createdAt: Date.now(),
          status: "streaming",
        };
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? touch({ ...c, messages: [...c.messages, msg] })
              : c,
          ),
        }));
        return msgId;
      },

      appendToMessage: (conversationId, messageId, delta) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId
                      ? { ...m, content: m.content + delta }
                      : m,
                  ),
                }
              : c,
          ),
        })),

      setMessageSources: (conversationId, messageId, sources) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId ? { ...m, sources } : m,
                  ),
                }
              : c,
          ),
        })),

      finalizeAssistantMessage: (conversationId, messageId, payload) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? touch({
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId
                      ? {
                          ...m,
                          content: payload.content,
                          sources: payload.sources,
                          metrics: payload.metrics,
                          status: "complete",
                        }
                      : m,
                  ),
                })
              : c,
          ),
        })),

      setMessageError: (conversationId, messageId, error) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId
                      ? { ...m, status: "error", error }
                      : m,
                  ),
                }
              : c,
          ),
        })),

      editUserMessage: (conversationId, messageId, content) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? touch({
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === messageId ? { ...m, content } : m,
                  ),
                })
              : c,
          ),
        })),

      removeMessage: (conversationId, messageId) =>
        set((s) => ({
          conversations: s.conversations.map((c) =>
            c.id === conversationId
              ? { ...c, messages: c.messages.filter((m) => m.id !== messageId) }
              : c,
          ),
        })),
    }),
    {
      name: "upi-rag-conversations",
      version: 1,
      // A tab/laptop that dies mid-answer leaves a message frozen in
      // "streaming" (or a "pending" turn with no assistant reply at all)
      // persisted to localStorage — on next load that rendered as an
      // infinite "sedang memproses" spinner with no way to recover. Convert
      // any such orphaned turn into a normal error state on rehydrate so the
      // usual edit/retry/copy affordances apply.
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        for (const conv of state.conversations) {
          for (let i = 0; i < conv.messages.length; i++) {
            const m = conv.messages[i];
            if (m.role === "assistant" && m.status === "streaming") {
              m.status = "error";
              m.error = "__interrupted__";
            }
          }
          const last = conv.messages[conv.messages.length - 1];
          if (last?.role === "user") {
            conv.messages.push({
              id: uid("msg_"),
              role: "assistant",
              content: "",
              createdAt: Date.now(),
              status: "error",
              error: "__interrupted__",
            });
          }
        }
      },
    },
  ),
);
