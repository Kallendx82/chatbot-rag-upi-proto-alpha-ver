"use client";

import { useEffect } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/backend-api";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error boundary:", error);
    try {
      void fetch(`${API_BASE}/api/client-error`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `${error.name}: ${error.message}${error.digest ? ` (digest ${error.digest})` : ""}`.slice(0, 2000),
          stack: error.stack?.slice(0, 20000) ?? null,
          url: window.location.href.slice(0, 2000),
        }),
        keepalive: true,
      }).catch(() => {});
    } catch {
      // Reporting must never throw inside the error boundary itself.
    }
  }, [error]);

  return (
    <html lang="id">
      <body style={{ fontFamily: "system-ui, sans-serif", padding: 40, textAlign: "center" }}>
        <h1 style={{ fontSize: 22, fontWeight: 600 }}>
          Server sedang dalam pemeliharaan
        </h1>
        <p style={{ color: "#666", marginTop: 8 }}>
          Mohon maaf atas ketidaknyamanannya. Silakan coba kembali beberapa saat lagi.
        </p>
        <button
          onClick={reset}
          style={{
            marginTop: 16, padding: "8px 16px", borderRadius: 8,
            background: "#1b3a6b", color: "white", border: "none", cursor: "pointer",
          }}
        >
          Coba lagi
        </button>
      </body>
    </html>
  );
}
