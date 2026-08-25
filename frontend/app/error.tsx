"use client";

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { BrandLogo } from "@/components/ui/BrandLogo";

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
    <div className="flex h-dvh flex-col items-center justify-center gap-5 bg-background px-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-surface-muted border border-border shadow-sm p-2">
        <BrandLogo className="h-16 w-16" iconClassName="h-10 w-10 text-primary" />
      </div>
      <div className="space-y-2">
        <h1 className="font-serif text-xl font-semibold text-foreground">
          Sistem Sedang Diperbarui / Sistem dalam Pemeliharaan
        </h1>
        <p className="max-w-md text-sm text-muted-foreground leading-relaxed">
          We&apos;re very sorry for the inconvenience. Our system right now is under maintenance. Please come back later, it will be finished soon.
        </p>
        <p className="max-w-md text-xs text-muted-foreground/60 leading-relaxed">
          Mohon maaf atas ketidaknyamanannya. Sistem kami saat ini sedang dalam pemeliharaan. Silakan kembali beberapa saat lagi, proses ini akan segera selesai.
        </p>
      </div>
      <Button onClick={reset} size="sm" className="mt-2">
        <RefreshCw className="h-3.5 w-3.5" />
        Coba lagi
      </Button>
    </div>
  );
}
