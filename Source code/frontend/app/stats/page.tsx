"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BarChart3, MessageSquareText, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { useMounted } from "@/hooks/useMounted";
import { ApiError, type StatsResponse } from "@/types";

/**
 * Admin-only question statistics. Aggregates come from the backend chat log
 * (all questions, including anonymous users), plus account/session counts.
 */
export default function StatsPage() {
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mounted || !token) return;
    api
      .stats(token)
      .then(setData)
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Gagal memuat statistik.",
        ),
      );
  }, [mounted, token]);

  if (!mounted) return null;

  if (!user || !user.is_admin) {
    return (
      <Shell>
        <p className="text-sm text-muted-foreground">
          Halaman ini hanya untuk admin. Silakan masuk dengan akun admin
          terlebih dahulu.
        </p>
      </Shell>
    );
  }

  if (error) {
    return (
      <Shell>
        <p className="text-sm text-destructive">{error}</p>
      </Shell>
    );
  }

  if (!data) {
    return (
      <Shell>
        <p className="text-sm text-muted-foreground">Memuat statistik…</p>
      </Shell>
    );
  }

  const maxDay = Math.max(1, ...data.questions_per_day.map((d) => d.count));
  const maxQ = Math.max(1, ...data.top_questions.map((q) => q.count));

  return (
    <Shell>
      {/* Ringkasan */}
      <div className="grid gap-3 sm:grid-cols-3">
        <MetricCard
          icon={<MessageSquareText className="h-4 w-4" />}
          label="Total pertanyaan"
          value={data.total_questions}
        />
        <MetricCard
          icon={<Users className="h-4 w-4" />}
          label="Akun terdaftar"
          value={data.total_users}
        />
        <MetricCard
          icon={<BarChart3 className="h-4 w-4" />}
          label="Sesi tersimpan"
          value={data.total_sessions}
        />
      </div>

      {/* Pertanyaan per hari */}
      <section>
        <h2 className="mb-3 font-serif text-lg font-semibold">
          Pertanyaan per hari
        </h2>
        {data.questions_per_day.length === 0 ? (
          <p className="text-sm text-muted-foreground">Belum ada data.</p>
        ) : (
          <div className="space-y-1.5">
            {data.questions_per_day.slice(-30).map((d) => (
              <div key={d.date} className="flex items-center gap-3">
                <span className="w-24 shrink-0 font-mono text-xs text-muted-foreground">
                  {d.date}
                </span>
                <div className="h-5 flex-1 overflow-hidden rounded bg-surface-muted">
                  <div
                    className="h-full rounded bg-primary"
                    style={{ width: `${(d.count / maxDay) * 100}%` }}
                  />
                </div>
                <span className="w-10 shrink-0 text-right font-mono text-xs tabular-nums">
                  {d.count}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Pertanyaan terpopuler */}
      <section>
        <h2 className="mb-3 font-serif text-lg font-semibold">
          Pertanyaan terpopuler
        </h2>
        {data.top_questions.length === 0 ? (
          <p className="text-sm text-muted-foreground">Belum ada data.</p>
        ) : (
          <ol className="space-y-2">
            {data.top_questions.map((q, i) => (
              <li
                key={q.question}
                className="rounded-lg border border-border bg-surface p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="min-w-0 flex-1 text-sm">
                    <span className="mr-2 font-mono text-xs text-muted-foreground">
                      #{i + 1}
                    </span>
                    {q.question}
                  </p>
                  <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 font-mono text-xs text-primary">
                    {q.count}×
                  </span>
                </div>
                <div className="mt-2 h-1.5 overflow-hidden rounded bg-surface-muted">
                  <div
                    className="h-full rounded bg-primary/60"
                    style={{ width: `${(q.count / maxQ) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-background">
      <header className="flex h-14 items-center gap-3 border-b-2 border-accent bg-primary px-4 dark:border-b dark:border-border dark:bg-surface/80">
        <Button
          variant="ghost"
          size="icon-sm"
          asChild
          className="text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:text-foreground dark:hover:bg-surface-muted"
        >
          <Link href="/" aria-label="Kembali ke chat">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <h1 className="font-serif text-base font-semibold text-primary-foreground dark:text-foreground">
          Statistik Pertanyaan
        </h1>
      </header>
      <main className="mx-auto max-w-3xl space-y-8 px-4 py-6">{children}</main>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-2 font-serif text-3xl font-semibold tabular-nums">
        {value.toLocaleString("id-ID")}
      </p>
    </div>
  );
}
