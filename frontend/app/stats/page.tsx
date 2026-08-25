"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, BarChart3, MessageSquareText, Users, ChevronDown, ChevronUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { useMounted } from "@/hooks/useMounted";
import { ApiError, type StatsResponse, type TopQuestion } from "@/types";

/**
 * Admin-only question statistics. Aggregates come from the backend chat log
 * (all questions, including anonymous users), plus account/session counts.
 */
import { LoadingScreen } from "@/components/ui/LoadingScreen";

export default function StatsPage() {
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const [data, setData] = useState<StatsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<"day" | "week" | "month" | "all">("all");
  const [popPage, setPopPage] = useState(1);
  const [dayPage, setDayPage] = useState(1);
  const [showUserList, setShowUserList] = useState(true);

  useEffect(() => {
    setPopPage(1);
  }, [timeRange]);

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

  if (!mounted) return <LoadingScreen />;

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
  const allDaysList = [...data.questions_per_day].reverse().slice(0, 30);
  const totalDayPages = Math.max(1, Math.ceil(allDaysList.length / 5));
  const currentDayList = allDaysList.slice((dayPage - 1) * 5, dayPage * 5);
  
  const topQuestions = 
    timeRange === "day" ? data.top_questions_day :
    timeRange === "week" ? data.top_questions_week :
    timeRange === "month" ? data.top_questions_month :
    data.top_questions;
    
  const maxQ = Math.max(1, ...topQuestions.map((q) => q.count));
  const totalPopPages = Math.max(1, Math.ceil(topQuestions.length / 5));
  const currentPopList = topQuestions.slice((popPage - 1) * 5, popPage * 5);

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
            {currentDayList.map((d) => (
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
            {totalDayPages > 1 && (
              <div className="mt-4 flex items-center justify-center gap-4 text-sm text-muted-foreground">
                <button
                  onClick={() => setDayPage(p => Math.max(1, p - 1))}
                  disabled={dayPage === 1}
                  className="p-1 hover:text-foreground disabled:opacity-50"
                >
                  {"<"}
                </button>
                <span>
                  {dayPage} / {totalDayPages} {dayPage === totalDayPages && "(halaman terakhir)"}
                </span>
                <button
                  onClick={() => setDayPage(p => Math.min(totalDayPages, p + 1))}
                  disabled={dayPage === totalDayPages}
                  className="p-1 hover:text-foreground disabled:opacity-50"
                >
                  {">"}
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Pertanyaan terpopuler */}
      <section>
        <div className="mb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="font-serif text-lg font-semibold">
            Pertanyaan terpopuler
          </h2>
          <div className="flex bg-surface-muted rounded p-1 space-x-1">
            <button 
              onClick={() => setTimeRange("day")} 
              className={`px-3 py-1 text-sm rounded ${timeRange === "day" ? "bg-surface shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >Hari</button>
            <button 
              onClick={() => setTimeRange("week")} 
              className={`px-3 py-1 text-sm rounded ${timeRange === "week" ? "bg-surface shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >Minggu</button>
            <button 
              onClick={() => setTimeRange("month")} 
              className={`px-3 py-1 text-sm rounded ${timeRange === "month" ? "bg-surface shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >Bulan</button>
            <button 
              onClick={() => setTimeRange("all")} 
              className={`px-3 py-1 text-sm rounded ${timeRange === "all" ? "bg-surface shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >Semua</button>
          </div>
        </div>
        
        {topQuestions.length === 0 ? (
          <p className="text-sm text-muted-foreground">Belum ada data.</p>
        ) : (
          <div className="space-y-2">
            <ol className="space-y-2">
              {currentPopList.map((q, i) => (
                <TopQuestionItem key={q.question} q={q} i={((popPage - 1) * 5) + i} maxQ={maxQ} />
              ))}
            </ol>
            {totalPopPages > 1 && (
              <div className="mt-6 flex flex-col items-center gap-4 text-sm text-muted-foreground">
                <div className="flex flex-wrap items-center justify-center gap-1">
                  <button
                    onClick={() => setPopPage(p => Math.max(1, p - 1))}
                    disabled={popPage === 1}
                    className="flex h-8 w-8 items-center justify-center rounded border border-border hover:bg-surface-muted hover:text-foreground disabled:opacity-50 disabled:hover:bg-transparent"
                  >
                    {"<"}
                  </button>
                  
                  {getPaginationRange(popPage, totalPopPages).map((p, idx) => {
                    if (p === "...") {
                      return (
                        <button
                          key={`dots-${idx}`}
                          onClick={() => {
                            const val = window.prompt(`Masukkan nomor halaman (1-${totalPopPages}):`);
                            if (val) {
                              const pageNum = parseInt(val, 10);
                              if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPopPages) {
                                setPopPage(pageNum);
                              }
                            }
                          }}
                          title="Lompat ke Halaman"
                          className="flex h-8 w-8 items-center justify-center rounded hover:bg-surface-muted hover:text-foreground cursor-pointer"
                        >
                          ...
                        </button>
                      );
                    }
                    const isCurrent = p === popPage;
                    return (
                      <button
                        key={p}
                        onClick={() => setPopPage(p as number)}
                        className={`flex h-8 w-8 items-center justify-center rounded border ${isCurrent ? "border-primary bg-primary text-primary-foreground font-medium" : "border-border hover:bg-surface-muted hover:text-foreground"}`}
                      >
                        {p}
                      </button>
                    );
                  })}

                  <button
                    onClick={() => setPopPage(p => Math.min(totalPopPages, p + 1))}
                    disabled={popPage === totalPopPages}
                    className="flex h-8 w-8 items-center justify-center rounded border border-border hover:bg-surface-muted hover:text-foreground disabled:opacity-50 disabled:hover:bg-transparent"
                  >
                    {">"}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Tabel Pengguna */}
      <section>
        <div className="mb-3 flex items-center gap-3">
          <h2 className="font-serif text-lg font-semibold">
            Daftar Pengguna
          </h2>
          <button 
            onClick={() => setShowUserList(!showUserList)} 
            className="rounded p-1 hover:bg-surface-muted text-muted-foreground"
          >
            {showUserList ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
        {showUserList && (
          <div className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-muted/50 font-medium text-muted-foreground">
                <tr>
                  <th className="p-3">Username</th>
                  <th className="p-3">Email</th>
                  <th className="p-3">Role</th>
                  <th className="p-3">Sesi Tersimpan</th>
                  <th className="p-3">Kuesioner/Feedback</th>
                  <th className="p-3">Akses Terakhir</th>
                  <th className="p-3">Dibuat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.users_list.map((u) => (
                  <tr key={u.id} className="hover:bg-surface-muted/30">
                    <td className="p-3 font-medium">{u.username}</td>
                    <td className="p-3 text-muted-foreground">{u.email || "-"}</td>
                    <td className="p-3">
                      {u.is_admin ? (
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary font-medium">Admin</span>
                      ) : u.email && (u.email.endsWith("@upi.edu") || u.email.endsWith("@student.upi.edu")) ? (
                        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary/80 font-medium">User / Sivitas UPI</span>
                      ) : (
                        <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs text-muted-foreground font-medium">User / Umum</span>
                      )}
                    </td>
                  <td className="p-3 tabular-nums">{u.session_count}</td>
                  <td className="p-3">
                    {u.feedback_satisfaction ? (
                      <div className="flex flex-col gap-0.5 text-xs">
                        <span className="font-medium text-foreground">
                          ⭐️ {u.feedback_satisfaction}/5 | Ease: {u.feedback_ease}/5
                        </span>
                        {u.feedback_text && (
                          <span
                            className="text-muted-foreground truncate max-w-[150px]"
                            title={u.feedback_text}
                          >
                            &quot;{u.feedback_text}&quot;
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="p-3 text-muted-foreground tabular-nums">
                    {u.last_active ? new Date(u.last_active).toLocaleString("id-ID") : "-"}
                  </td>
                  <td className="p-3 text-muted-foreground tabular-nums">
                    {new Date(u.created_at).toLocaleString("id-ID")}
                  </td>
                </tr>
              ))}
              {data.users_list.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-4 text-center text-muted-foreground">
                    Belum ada data pengguna.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
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

function TopQuestionItem({ q, i, maxQ }: { q: TopQuestion; i: number; maxQ: number }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <li className="rounded-lg border border-border bg-surface flex flex-col overflow-hidden">
      <button 
        className="p-3 w-full text-left flex flex-col hover:bg-surface-muted/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3 w-full">
          <p className="min-w-0 flex-1 text-sm">
            <span className="mr-2 font-mono text-xs text-muted-foreground">
              #{i + 1}
            </span>
            {q.question}
          </p>
          <div className="flex items-center gap-2">
            <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 font-mono text-xs text-primary">
              {q.count}×
            </span>
            {expanded ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </div>
        </div>
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded bg-surface-muted">
          <div
            className="h-full rounded bg-primary/60"
            style={{ width: `${(q.count / maxQ) * 100}%` }}
          />
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 border-t border-border pt-3 bg-surface">
          <div className="overflow-x-auto rounded border border-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-muted/50 font-medium text-muted-foreground">
                <tr>
                  <th className="p-2">Waktu</th>
                  <th className="p-2 text-right">Respon</th>
                  <th className="p-2 text-right">Retrieval</th>
                  <th className="p-2 text-right">LLM</th>
                  <th className="p-2 text-right">Model</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {q.latency_records?.map((r, idx) => (
                  <tr key={idx} className="hover:bg-surface-muted/30">
                    <td className="p-2 text-muted-foreground whitespace-nowrap">
                      {new Date(r.ts).toLocaleString("id-ID")}
                    </td>
                    <td className="p-2 tabular-nums text-right">{(r.total_ms / 1000).toFixed(2)}s</td>
                    <td className="p-2 tabular-nums text-muted-foreground text-right">{(r.retrieval_ms / 1000).toFixed(2)}s</td>
                    <td className="p-2 tabular-nums text-muted-foreground text-right">{(r.generation_ms / 1000).toFixed(2)}s</td>
                    <td className="p-2 text-muted-foreground text-right">{r.backend || "-"}</td>
                  </tr>
                ))}
                {(!q.latency_records || q.latency_records.length === 0) && (
                  <tr>
                    <td colSpan={5} className="p-2 text-center text-muted-foreground">
                      Data latency tidak tersedia
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </li>
  );
}

function getPaginationRange(current: number, total: number) {
  const range: (number | string)[] = [];
  const delta = 2; // number of pages to show before and after current page
  
  range.push(1);
  
  if (current - delta > 2) {
    range.push("...");
  }
  
  const start = Math.max(2, current - delta);
  const end = Math.min(total - 1, current + delta);
  
  for (let i = start; i <= end; i++) {
    range.push(i);
  }
  
  if (current + delta < total - 1) {
    range.push("...");
  }
  
  if (total > 1) {
    range.push(total);
  }
  
  return range;
}
