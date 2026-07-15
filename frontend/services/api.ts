/**
 * Typed API client for the UPI RAG FastAPI backend (Slice 1 contract).
 *
 * Base URL comes from NEXT_PUBLIC_API_BASE_URL. In development this defaults to
 * the Next.js rewrite path "/backend-api" (see next.config.mjs), which proxies
 * to the backend and sidesteps CORS. In production, point it at the deployed
 * backend origin.
 *
 * Endpoints used (real, verified against Slice 1):
 *   GET  /health
 *   POST /api/chat
 *   POST /api/retrieve
 *   GET  /api/retrieve/debug?query=...&top_k=...
 *
 * Streaming note: the backend does NOT yet expose /api/chat/stream (deferred to
 * a later slice). `streamChat` is written so that when that endpoint lands, only
 * the marked block changes; today it falls back to the non-streaming /api/chat
 * and emits the answer progressively on the client (see useChat hook).
 */
import {
  ApiError,
  type AuthResponse,
  type ChatRequest,
  type ChatResponse,
  type HealthResponse,
  type RetrievalDebugResponse,
  type RetrieveRequest,
  type RetrieveResponse,
  type ServerSessionDetail,
  type ServerSessionSummary,
  type StatsResponse,
  type StoredMessage,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/backend-api";

/** Core fetch wrapper: JSON in/out, uniform error handling, timeouts. */
async function request<T>(
  path: string,
  options: RequestInit & { timeoutMs?: number; signal?: AbortSignal } = {},
): Promise<T> {
  const { timeoutMs = 60_000, signal: externalSignal, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  // Relay an external (caller) abort — e.g. the user pressing Stop — onto the
  // internal controller so the actual network request is cancelled, not just
  // the local timeout.
  const relay = () => controller.abort();
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener("abort", relay, { once: true });
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(init.headers || {}),
      },
    });
  } catch (err) {
    clearTimeout(timer);
    externalSignal?.removeEventListener("abort", relay);
    if (err instanceof DOMException && err.name === "AbortError") {
      // Distinguish a user cancellation (status -2) from a timeout (408) so the
      // caller can drop the message silently instead of showing an error.
      if (externalSignal?.aborted) {
        throw new ApiError("Dibatalkan oleh pengguna.", -2);
      }
      throw new ApiError("Permintaan melebihi batas waktu (timeout).", 408);
    }
    // Network failure / backend down.
    throw new ApiError(
      "Tidak dapat terhubung ke server. Pastikan backend berjalan.",
      0,
      err,
    );
  }
  clearTimeout(timer);
  externalSignal?.removeEventListener("abort", relay);

  if (!res.ok) {
    let detail: unknown = undefined;
    try {
      detail = await res.json();
    } catch {
      /* response had no JSON body */
    }
    const message =
      (detail as { detail?: string })?.detail ||
      `Permintaan gagal (HTTP ${res.status}).`;
    throw new ApiError(
      typeof message === "string" ? message : `HTTP ${res.status}`,
      res.status,
      detail,
    );
  }

  return (await res.json()) as T;
}

export const api = {
  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/health", {
      method: "GET",
      timeoutMs: 8_000,
    });
  },

  chat(body: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
    return request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify(body),
      timeoutMs: 120_000,
      signal,
    });
  },

  retrieve(body: RetrieveRequest, signal?: AbortSignal): Promise<RetrieveResponse> {
    return request<RetrieveResponse>("/api/retrieve", {
      method: "POST",
      body: JSON.stringify(body),
      signal,
    });
  },

  retrieveDebug(
    query: string,
    topK?: number,
    scoreThreshold?: number,
    language: "id" | "en" = "id",
  ): Promise<RetrievalDebugResponse> {
    const params = new URLSearchParams({ query, language });
    if (topK != null) params.set("top_k", String(topK));
    if (scoreThreshold != null) params.set("score_threshold", String(scoreThreshold));
    return request<RetrievalDebugResponse>(
      `/api/retrieve/debug?${params.toString()}`,
      { method: "GET" },
    );
  },

  // --- auth ---------------------------------------------------------------
  register(username: string, password: string, email: string): Promise<AuthResponse> {
    return request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password, email }),
      timeoutMs: 15_000,
    });
  },

  login(username: string, password: string): Promise<AuthResponse> {
    return request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
      timeoutMs: 15_000,
    });
  },

  logout(token: string): Promise<void> {
    return requestVoid("/api/auth/logout", {
      method: "POST",
      headers: authHeader(token),
      timeoutMs: 10_000,
    });
  },

  // --- server-saved chat sessions ------------------------------------------
  listSessions(token: string): Promise<ServerSessionSummary[]> {
    return request<ServerSessionSummary[]>("/api/sessions", {
      method: "GET",
      headers: authHeader(token),
      timeoutMs: 15_000,
    });
  },

  createSession(
    token: string,
    id: string,
    title: string,
  ): Promise<ServerSessionSummary> {
    return request<ServerSessionSummary>("/api/sessions", {
      method: "POST",
      headers: authHeader(token),
      body: JSON.stringify({ id, title }),
      timeoutMs: 15_000,
    });
  },

  getSession(token: string, id: string): Promise<ServerSessionDetail> {
    return request<ServerSessionDetail>(
      `/api/sessions/${encodeURIComponent(id)}`,
      { method: "GET", headers: authHeader(token), timeoutMs: 20_000 },
    );
  },

  renameSession(token: string, id: string, title: string): Promise<unknown> {
    return request<unknown>(`/api/sessions/${encodeURIComponent(id)}`, {
      method: "PUT",
      headers: authHeader(token),
      body: JSON.stringify({ title }),
      timeoutMs: 10_000,
    });
  },

  deleteSession(token: string, id: string): Promise<void> {
    return requestVoid(`/api/sessions/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: authHeader(token),
      timeoutMs: 10_000,
    });
  },

  saveMessages(
    token: string,
    id: string,
    messages: StoredMessage[],
  ): Promise<unknown> {
    return request<unknown>(
      `/api/sessions/${encodeURIComponent(id)}/messages`,
      {
        method: "PUT",
        headers: authHeader(token),
        body: JSON.stringify({ messages }),
        timeoutMs: 20_000,
      },
    );
  },

  // --- stats (admin) --------------------------------------------------------
  stats(token: string): Promise<StatsResponse> {
    return request<StatsResponse>("/api/stats", {
      method: "GET",
      headers: authHeader(token),
      timeoutMs: 20_000,
    });
  },
};

function authHeader(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` };
}

/** Like request<T> but tolerates empty (204) response bodies. */
async function requestVoid(
  path: string,
  options: RequestInit & { timeoutMs?: number } = {},
): Promise<void> {
  const { timeoutMs = 15_000, ...init } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      signal: controller.signal,
      headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    });
    if (!res.ok && res.status !== 204) {
      throw new ApiError(`Permintaan gagal (HTTP ${res.status}).`, res.status);
    }
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("Permintaan melebihi batas waktu (timeout).", 408);
    }
    throw new ApiError("Tidak dapat terhubung ke server.", 0, err);
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Streaming chat.
 *
 * Contract: yields incremental text deltas, then resolves with the full
 * ChatResponse (including sources + metrics) via the onComplete callback.
 *
 * TODAY: there is no SSE endpoint, so this calls /api/chat once and the caller
 * (useChat) animates the text. When the backend gains /api/chat/stream, replace
 * ONLY the body of this function with an EventSource/ReadableStream reader that
 * yields deltas as they arrive; the hook's interface does not change.
 */
export async function fetchChat(
  body: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return api.chat(body, signal);
}
