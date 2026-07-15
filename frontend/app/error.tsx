"use client";

import { useEffect } from "react";
import { RefreshCw, Wrench } from "lucide-react";

import { Button } from "@/components/ui/button";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/backend-api";

/** Fire-and-forget crash report; the UI never blocks or surfaces this. */
function reportToBackend(error: Error & { digest?: string }) {
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
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Full detail goes to the backend log; users only see the generic
    // maintenance message below.
    console.error("App error boundary:", error);
    reportToBackend(error);
  }, [error]);

  return (
    <div className="flex h-dvh flex-col items-center justify-center gap-4 bg-background px-4 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/15 text-accent-foreground">
        <Wrench className="h-7 w-7" />
      </div>
      <div>
        <h1 className="font-serif text-xl font-semibold">
          Server sedang dalam pemeliharaan
        </h1>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          Mohon maaf atas ketidaknyamanannya. Silakan coba kembali beberapa
          saat lagi.
        </p>
      </div>
      <Button onClick={reset}>
        <RefreshCw className="h-4 w-4" />
        Coba lagi
      </Button>
    </div>
  );
}
