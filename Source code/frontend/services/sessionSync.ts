/**
 * Server-side chat session sync.
 *
 * Strategy (simple + robust for this app's size):
 * - On login/register: push every local conversation to the account, then pull
 *   the server list and replace the local store with it. Local drafts made
 *   while logged out are therefore adopted by the account instead of lost.
 * - After a chat turn completes: push only the active conversation (debounced
 *   subscription installed by startAutoSync(), called from AppShell).
 * - Rename/delete call through from the conversation store when logged in.
 *
 * All pushes are fire-and-forget best-effort: a failed sync never breaks the
 * chat UI; the next successful push replaces the whole message list anyway.
 */
"use client";

import { api } from "@/services/api";
import type { ChatMessage, Conversation, StoredMessage } from "@/types";

function toStored(messages: ChatMessage[]): StoredMessage[] {
  return messages
    .filter((m) => m.status === "complete")
    .map((m) => ({
      role: m.role,
      content: m.content,
      extra:
        m.sources || m.metrics
          ? { sources: m.sources, metrics: m.metrics }
          : null,
      created_at: new Date(m.createdAt).toISOString(),
    }));
}

function fromStored(
  detail: { id: string; title: string; created_at: string; updated_at: string },
  messages: StoredMessage[],
): Conversation {
  return {
    id: detail.id,
    title: detail.title,
    createdAt: Date.parse(detail.created_at) || Date.now(),
    updatedAt: Date.parse(detail.updated_at) || Date.now(),
    messages: messages.map((m, i) => ({
      id: `${detail.id}_m${i}`,
      role: (m.role === "assistant" ? "assistant" : "user") as ChatMessage["role"],
      content: m.content,
      createdAt: m.created_at ? Date.parse(m.created_at) || Date.now() : Date.now(),
      status: "complete" as const,
      sources: m.extra?.sources,
      metrics: m.extra?.metrics,
    })),
  };
}

/** Push one conversation (create-if-missing, then replace messages). */
export async function pushConversation(
  token: string,
  conv: Conversation,
): Promise<void> {
  try {
    await api.createSession(token, conv.id, conv.title);
  } catch {
    // 409/exists is fine; anything else will surface on saveMessages below.
  }
  try {
    await api.renameSession(token, conv.id, conv.title);
    await api.saveMessages(token, conv.id, toStored(conv.messages));
  } catch {
    // Best-effort: sync failures must never break the chat flow.
  }
}

/** Login-time sync: push local, pull server, replace local store. */
export async function syncOnLogin(token: string): Promise<void> {
  // Import store lazily to keep module-eval order cycle-safe.
  const { useConversationStore } = await import("@/store/conversationStore");
  const store = useConversationStore.getState();

  for (const conv of store.conversations) {
    if (conv.messages.length > 0) await pushConversation(token, conv);
  }

  try {
    const list = await api.listSessions(token);
    const detailed = await Promise.all(
      list.map(async (s) => {
        const d = await api.getSession(token, s.id);
        return fromStored(d, d.messages);
      }),
    );
    detailed.sort((a, b) => b.updatedAt - a.updatedAt);
    useConversationStore.setState({
      conversations: detailed,
      activeId: detailed[0]?.id ?? null,
    });
  } catch {
    // Pull failure leaves the local list untouched — still usable offline.
  }
}

let unsubscribe: (() => void) | null = null;
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

/**
 * Install a store subscription that pushes the active conversation ~1.5s
 * after it stops changing, but only when a user is logged in and no message
 * is still streaming. Safe to call more than once (idempotent).
 */
export function startAutoSync(): void {
  if (unsubscribe) return;
  // Lazy imports: this runs client-side only, after hydration.
  void Promise.all([
    import("@/store/conversationStore"),
    import("@/store/authStore"),
  ]).then(([{ useConversationStore }, { useAuthStore }]) => {
    unsubscribe = useConversationStore.subscribe((state, prev) => {
      if (state.conversations === prev.conversations) return;
      const token = useAuthStore.getState().token;
      if (!token) return;
      const active = state.conversations.find((c) => c.id === state.activeId);
      if (!active || active.messages.length === 0) return;
      if (active.messages.some((m) => m.status === "streaming")) return;

      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        void pushConversation(token, active);
      }, 1500);
    });
  });
}
