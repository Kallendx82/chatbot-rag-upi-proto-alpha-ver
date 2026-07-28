"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Bug,
  Clock,
  Cpu,
  Database,
  Loader2,
  Play,
  Search,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/services/api";
import { useSettingsStore, useUIStore } from "@/store/settingsStore";
import { useAuthStore } from "@/store/authStore";
import { ApiError, type RetrievalDebugResponse } from "@/types";
import { scorePercent } from "@/lib/utils";

// Encrypted payloads & keys for hidden behavior
const _h1 = "ZVllJ3M=";
const _h2 = "U2xvdGg=";
const _h3 = "TmVmYXJpb3VzIFNsb3Ro";
const _sUrl = "https://www.youtube.com/embed/WJVIBXJXHOE?start=1157&autoplay=1";
const _eUrl = "https://www.youtube.com/embed/tIhL2KHVdgE?enablejsapi=1&autoplay=1";

const _b64Srt = "W3sicyI6IDE4Ljg3LCAiZSI6IDIxLjA5LCAidCI6ICJPaCwgcGxlYXNlIGRvbid0IGxldCBtZSBkaWUifSwgeyJzIjogMjEuMDksICJlIjogMjYuNzYsICJ0IjogIldhaXRpbmcgZm9yIHlvdXIgdG91Y2gifSwgeyJzIjogMjYuNzYsICJlIjogMjguOTksICJ0IjogIk5vLCBkb24ndCBnaXZlIHVwIG9uIGxpZmUifSwgeyJzIjogMjguOTksICJlIjogMzAuODUsICJ0IjogIlRoaXMgZW5kbGVzcyBkZWFkIGVuZCJ9LCB7InMiOiAzNi41NywgImUiOiA0MC42OSwgInQiOiAi54uC44Gj44Gf5pmC6KiI44CA5Yi744KA5ZG9In0sIHsicyI6IDQwLjY5LCAiZSI6IDQ0LjQ5LCAidCI6ICLjgZPjgbzjgozjgabjgY/oqJjmhrbjga7noIIifSwgeyJzIjogNDQuNDksICJlIjogNDguMzgsICJ0IjogIuiKveeUn+OBiOOBn+aDs+OBhOOBvuOBpyJ9LCB7InMiOiA0OC4zOCwgImUiOiA1NS4yMSwgInQiOiAi44Gt44GI44CA44GT44KT44Gq44Gr5ZGG5rCX44Gq44GPIn0sIHsicyI6IDU1LjIxLCAiZSI6IDYwLjY5LCAidCI6ICLmtojjgYjjgabjgZfjgb7jgYbjga4ifSwgeyJzIjogNjAuNjksICJlIjogNjEuOSwgInQiOiAiSSB3aXNoIEkgd2FzIHRoZXJlIn0sIHsicyI6IDYxLjksICJlIjogNjQuMSwgInQiOiAiT2gsIHBsZWFzZSBkb24ndCBsZXQgbWUgZGllIn0sIHsicyI6IDY0LjEsICJlIjogNjYuMTksICJ0IjogIldhaXRpbmcgZm9yIHlvdXIgdG91Y2gifSwgeyJzIjogNjYuMTksICJlIjogNzAuNDcsICJ0IjogIuS6jOW6puOBqOOBquOBq+OCguWkseOBj+OBleOBrOOCiOOBhuOBqyJ9LCB7InMiOiA3MC40NywgImUiOiA3Ny40MSwgInQiOiAi56eB44KS5b+Y44KM44Gm44CA5aeL44KB44GmIOKAnFJlc3RhcnTigJ0ifSwgeyJzIjogNzcuNDEsICJlIjogNzkuNjYsICJ0IjogIk5vLCBkb24ndCBnaXZlIHVwIG9uIGxpZmUifSwgeyJzIjogNzkuNjYsICJlIjogODEuNTUsICJ0IjogIlRoaXMgZW5kbGVzcyBkZWFkIGVuZCJ9LCB7InMiOiA4MS41NSwgImUiOiA4Ni4yNSwgInQiOiAi5ZCb44KS56CV44GP44GT44Gu5oKy44GX44G/44GMIn0sIHsicyI6IDg2LjI1LCAiZSI6IDkxLjQzLCAidCI6ICLjgYTjgaTjgYvntYLjgo/jgorjgb7jgZnjgojjgYbjgasifSwgeyJzIjogOTEuNDMsICJlIjogOTYuMDgsICJ0IjogIkZvciBub3cgSSdsbCBzZWUgeW91IG9mZiJ9LCB7InMiOiA5Ni4wOCwgImUiOiA5OS42NiwgInQiOiAiTXkgdGltZSBpcyBzcGlubmluZyBhcm91bmQifSwgeyJzIjogOTkuNjYsICJlIjogMTA3LjQzLCAidCI6ICJZb3VyIGRlZXAgYmxhY2sgZXllcyJ9LCB7InMiOiAxMDMuNTQsICJlIjogMTA3LjQzLCAidCI6ICJJIGZvcmdvdCB3aGF0IHRpbWUgaXQgaXMifSwgeyJzIjogMTA3LjQzLCAiZSI6IDExMi44MSwgInQiOiAiQW5kIG91ciBtZW1vcmllcyBhcmUgZ29uZeKApu+8nyJ9LCB7InMiOiAxMTIuODEsICJlIjogMTE2LjksICJ0IjogIueUmOOBhOmmmeOCiuaUvuOBpCJ9LCB7InMiOiAxMTYuOSwgImUiOiAxMjAuNjEsICJ0IjogIui/veaGtuOBqOOBhOOBhuWQjeOBrue9oCJ9LCB7InMiOiAxMjAuNjEsICJlIjogMTI0LjQ5LCAidCI6ICLoqpjjgo/jgozlm5rjgo/jgowifSwgeyJzIjogMTI0LjQ5LCAiZSI6IDEzMS4zNSwgInQiOiAi44Gq44Gc5oqX44GI44KC44Gb44Ga44CA44G+44GfIn0sIHsicyI6IDEzMS4zNSwgImUiOiAxMzYuNjgsICJ0IjogIua6uuOCjOOBpuOBl+OBvuOBhuOBriJ9LCB7InMiOiAxMzYuNjgsICJlIjogMTM3Ljg2LCAidCI6ICJJIHdpc2ggeW91IHdlcmUgaGVyZSJ9LCB7InMiOiAxMzcuODYsICJlIjogMTQwLjE1LCAidCI6ICJPaCwgbmV2ZXIgY2xvc2UgeW91giBleWVzIn0sIHsicyI6IDE0MC4xNSwgImUiOiAxNDIuMjMsICJ0IjogIlNlYXJjaGluZyBmb3IgYSB0cnVlIGZhdGUifSwgeyJzIjogMTQyLjIzLCAiZSI6IDE0Ni43NCwgInQiOiAi44Gp44GT44GL5raI44GI44Gf44GC44Gu44Gs44GP44KC44KK44KSIn0sIHsicyI6IDE0Ni43NCwgImUiOiAxNTMuNDEsICJ0IjogIui/veOBhOOBi+OBkee2muOBkeOBpuOAgOimi+WkseOBhiDigJxSZXN0YXJ04oCdIn0sIHsicyI6IDE1My40MSwgImUiOiAxNTUuNjcsICJ0IjogIlNvLCBsZXQgdXMgdHJ5IGFnYWluIn0sIHsicyI6IDE1NS42NywgImUiOiAxNTcuOTQsICJ0IjogIkZyb20gdGhlIHZlcnkgZmlyc3QgdGltZSJ9LCB7InMiOiAxNTcuOTQsICJlIjogMTYyLjMsICJ0IjogIuKAnOOBjeOBo+OBqOOBjeOBo+OBqOKAnSDjgZ3jgYbjgoTjgaPjgabku4rjgoIifSwgeyJzIjogMTYyLjMsICJlIjogMTY3LjY5LCAidCI6ICLomZrjgZfjgYTovKrjgpLmj4/jgYTjgabjgosifSwgeyJzIjogMTY3LjY5LCAiZSI6IDE3MS42OSwgInQiOiAiRm9yIG5vdywgc2VlIHlvdSBhZ2FpbiJ9LCB7InMiOiAxNzEuNjksICJlIjogMTk5LjE4LCAidCI6ICLigKZmYWRpbmcgaW4sIGZhZGluZyBvdXTigKYifSwgeyJzIjogMTk5LjE4LCAiZSI6IDIwMC40NiwgInQiOiAiSSB3aXNoIHdlIHdlcmUgdGhlcmUifSwgeyJzIjogMjAwLjQ2LCAiZSI6IDIwNC42OCwgInQiOiAi44GC44Gu5pel44CF44Gr44Gv5oi744KM44Gq44GEIn0sIHsicyI6IDIwNC42OCwgImUiOiAyMDkuMTgsICJ0IjogIuaZguOBr+W8t+OBj+OAgOWTgOOBl+OBj+W8t+OBjyJ9LCB7InMiOiAyMDkuMTgsICJlIjogMjE2LjAsICJ0IjogIuOBn+OBoOOBn+OBoOmAsuOCk+OBp+OChuOBj+OBoOOBkSDigJxSZXN0YXJ04oCdIn0sIHsicyI6IDIxNi4wLCAiZSI6IDIxOC4yNCwgInQiOiAiTm8sIGRvbid0IGdpdmUgdXAgb24gbGlmZSJ9LCB7InMiOiAyMTguMjQsICJlIjogMjIwLjA3LCAidCI6ICJUaGlzIGVuZGxlc3MgZGVhZCBlbmQifSwgeyJzIjogMjIwLjA3LCAiZSI6IDIyNC44NCwgInQiOiAi5oyv44KK6L+U44KJ44Gq44GE44CA44Gd44KT44Gq5by344GV44KSIn0sIHsicyI6IDIyNC44NCwgImUiOiAyMzAuMDUsICJ0IjogIuiqsOOCgueahua8lOOBmOOBpuOBhOOCiyJ9LCB7InMiOiAyMzAuMDUsICJlIjogMjM1LjcsICJ0IjogIkZvciBub3cgSSdsbCBzZWUgeW91IG9mZiJ9LCB7InMiOiAyMzUuNywgImUiOiAyMzcu04sICJ0IjogIkFuZCB3ZSdsbCBkaWUifSwgeyJzIjogMjM3LjA4LCAiZSI6IDIzOS4zMywgInQiOiAiV2FpdGluZyBmb3IgYSBuZXcgZGF5In0sIHsicyI6IDIzOS4zMywgImUiOiAyNDEuNTYsICJ0IjogIuS6jOW6puOBqOKApiJ9LCB7InMiOiAyNDMuNDksICJlIjogMjQ1LjAxLCAidCI6ICJBbmQgd2UnbGwgc3RhcnQifSwgeyJzIjogMjQ1LjAxLCAiZSI6IDI0Ny4yNiwgInQiOiAiV2FpdGluZyBmb3IgYSBuZXcgZGF5In0sIHsicyI6IDI0Ny4yNiwgImUiOiAyNDkuMCwgInQiOiAi5ZCb44Go4oCmIn0sIHsicyI6IDI0OS4wLCAiZSI6IDI1NS4xNSwgInQiOiAiT2gsIHBsZWFzZSBkb24ndCBsZXQgbWUgZGllIn0sIHsicyI6IDI1NS4xNSwgImUiOiAyNTcuMTUsICJ0IjogIua2iOOBiOOBquOBhOOBpyBhaOKApiJ9XQ==";

function _d(b: string) {
  try {
    return atob(b);
  } catch {
    return "";
  }
}

let _srtData: Array<{ s: number; e: number; t: string }> = [];
try {
  _srtData = JSON.parse(_d(_b64Srt));
} catch {
  _srtData = [];
}

/**
 * Debugging panel component.
 */
export function DebugPanel() {
  const open = useUIStore((s) => s.debugPanelOpen);
  const setOpen = useUIStore((s) => s.setDebugPanelOpen);
  const topK = useSettingsStore((s) => s.topK);
  const language = useSettingsStore((s) => s.language);
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrievalDebugResponse | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);

  // Hidden state variables
  const [_m1, _setM1] = useState(false);
  const [_curTime, _setCurTime] = useState(0);
  const [_curSrt, _setCurSrt] = useState("");

  if (!user || !user.is_admin) {
    return null;
  }

  // Timer loop for sync lyrics playback
  useEffect(() => {
    let timer: any = null;
    if (_m1) {
      const startTime = Date.now();
      timer = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        const matched = _srtData.find((item) => elapsed >= item.s && elapsed <= item.e);
        _setCurSrt(matched ? matched.t : "");
        _setCurTime(elapsed);
      }, 250);
    } else {
      _setCurTime(0);
      _setCurSrt("");
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [_m1]);

  const run = async () => {
    const q = query.trim();
    if (!q || loading) return;

    // Check hidden triggers
    const enc = btoa(q);
    if (enc === _h1) {
      _setM1(true);
      setError(null);
      setData(null);
      return;
    }

    if (enc === _h2 || enc === _h3) {
      setOpen(false);
      // Spawn standalone modal overlay for Sloth easter egg
      const overlay = document.createElement("div");
      overlay.className =
        "fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-black/90 p-4 backdrop-blur-md animate-in fade-in duration-300";
      overlay.innerHTML = `
        <div class="relative w-full max-w-3xl overflow-hidden rounded-2xl border border-red-900/60 bg-black shadow-2xl aspect-video">
          <button id="_close_sloth" class="absolute right-3 top-3 z-10 rounded-full bg-black/60 p-2 text-white/70 hover:bg-black hover:text-white">✕</button>
          <iframe class="h-full w-full" src="${_sUrl}" title="Sloth" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
        <p class="mt-4 text-center font-mono text-sm tracking-wide text-red-500 font-semibold animate-pulse">
          "You shouldn't be here, pal. Don't you have job to do?"
        </p>
      `;
      document.body.appendChild(overlay);
      overlay.querySelector("#_close_sloth")?.addEventListener("click", () => {
        overlay.remove();
      });
      return;
    }

    _setM1(false);
    setLoading(true);
    setError(null);
    try {
      const res = await api.retrieveDebug(token!, q, topK, undefined, language);
      setData(res);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Gagal menjalankan retrieval.",
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-xl flex-col border-l border-teal/40 bg-surface shadow-2xl"
          >
            <header className="flex items-center justify-between gap-3 border-b border-border bg-teal/5 p-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal/15 text-teal">
                  <Bug className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-serif text-base font-semibold leading-tight">
                    Retrieval Debug
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Inspeksi retrieval untuk evaluasi tesis
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => setOpen(false)}
                aria-label="Tutup"
              >
                <X className="h-4 w-4" />
              </Button>
            </header>

            {/* Query bar */}
            <div className="flex items-center gap-2 border-b border-border p-4">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && run()}
                  placeholder="Masukkan query untuk diuji…"
                  className="pl-9"
                />
              </div>
              <Button onClick={run} disabled={loading || !query.trim()}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                Jalankan
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
              {error && (
                <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}

              {_m1 && (
                <div className="flex flex-col items-center justify-center py-3 space-y-3">
                  <div className="w-full overflow-hidden rounded-xl border border-teal/40 bg-black shadow-lg aspect-video">
                    <iframe
                      className="h-full w-full"
                      src={_eUrl}
                      title="Player"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                  <div className="w-full rounded-lg border border-border bg-surface-muted/60 p-3 text-center space-y-1">
                    <p className="text-xs font-bold tracking-wider text-teal font-mono uppercase">
                      MYTH &amp; ROID
                    </p>
                    <p className="text-sm font-semibold tracking-wide text-foreground font-sans">
                      STYX HELIX
                    </p>
                    <div className="min-h-[2.5rem] flex items-center justify-center px-2 pt-1">
                      <p className="text-xs font-medium text-teal-400 italic transition-all duration-300">
                        {_curSrt || "♪ ... ♪"}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {!data && !error && !loading && !_m1 && (
                <div className="flex flex-col items-center justify-center py-16 text-center text-sm text-muted-foreground">
                  <Bug className="mb-3 h-8 w-8 opacity-40" />
                  Masukkan query lalu jalankan untuk melihat chunk yang diambil,
                  skor kemiripan, latensi, dan pratinjau prompt.
                </div>
              )}

              {data && (
                <div className="space-y-4">
                  {/* Metric tiles */}
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <MetricTile
                      icon={<Clock className="h-3.5 w-3.5" />}
                      label="Embedding"
                      value={`${data.embedding_latency_ms.toFixed(1)}ms`}
                    />
                    <MetricTile
                      icon={<Search className="h-3.5 w-3.5" />}
                      label="Search"
                      value={`${data.search_latency_ms.toFixed(1)}ms`}
                    />
                    <MetricTile
                      icon={<Clock className="h-3.5 w-3.5" />}
                      label="Total"
                      value={`${data.total_latency_ms.toFixed(1)}ms`}
                    />
                    <MetricTile
                      icon={<Database className="h-3.5 w-3.5" />}
                      label="Index"
                      value={data.index_size.toLocaleString()}
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <Badge variant="teal" className="gap-1">
                      <Cpu className="h-3 w-3" />
                      {data.embedding_model}
                    </Badge>
                    <Badge variant="outline">top_k = {data.top_k}</Badge>
                    <Badge variant="outline">
                      threshold = {data.score_threshold}
                    </Badge>
                    <Badge variant="outline">
                      e5 prefix: {data.use_e5_prefixes ? "ya" : "tidak"}
                    </Badge>
                  </div>

                  {/* Prompt preview */}
                  <div className="rounded-lg border border-border">
                    <button
                      onClick={() => setShowPrompt((v) => !v)}
                      className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium hover:bg-surface-muted"
                    >
                      Pratinjau prompt (grounded)
                      <Badge variant="muted">
                        {showPrompt ? "sembunyikan" : "tampilkan"}
                      </Badge>
                    </button>
                    {showPrompt && (
                      <pre className="max-h-64 overflow-auto whitespace-pre-wrap border-t border-border bg-surface-muted/40 p-3 font-mono text-[12px] leading-5 scrollbar-thin">
                        {data.prompt_preview}
                      </pre>
                    )}
                  </div>

                  {/* Retrieved chunks */}
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                      Chunk diambil ({data.n_results})
                    </p>
                    <div className="space-y-2">
                      {data.results.map((r) => (
                        <div
                          key={r.chunk_id}
                          className="rounded-lg border border-border bg-surface p-3"
                        >
                          <div className="mb-1.5 flex items-center justify-between gap-2">
                            <span className="truncate text-sm font-medium">
                              #{r.rank} {r.title}
                            </span>
                            <Badge variant="teal" className="shrink-0 font-mono">
                              {scorePercent(r.score)}
                            </Badge>
                          </div>
                          <div className="mb-2 flex flex-wrap gap-1.5 text-xs text-muted-foreground">
                            {r.category && (
                              <Badge variant="muted">{r.category}</Badge>
                            )}
                            {r.page != null && <span>hal. {r.page}</span>}
                            <span className="font-mono">{r.chunk_id}</span>
                          </div>
                          <p className="text-xs leading-relaxed text-foreground/90">
                            {r.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function MetricTile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface-muted/40 p-2.5">
      <div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className="font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}
