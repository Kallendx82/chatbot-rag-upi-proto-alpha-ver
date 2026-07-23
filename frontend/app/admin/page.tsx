"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, CheckCircle2, AlertCircle, Plus, ChevronDown, ChevronUp, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { useMounted } from "@/hooks/useMounted";

const DEFAULT_CATEGORIES = [
  "PPID UPI",
  "PMB UPI",
  "LPPM UPI",
  "Direktorat Pendidikan",
  "UPI Kampus Cibiru",
  "UPI Kampus Sumedang",
  "UPI Kampus Tasikmalaya",
  "UPI Kampus Purwakarta",
  "UPI Kampus Serang",
  "Dokumen Kepegawaian dan regulasi institusi",
];

const CUSTOM_CATEGORY_KEY = "__custom__";

const BG_IMAGES = [
  "/backgrounds/isola.jpg",
  "/backgrounds/upi-kampus-cibiru.jpg",
  "/backgrounds/sumedang.jpg",
  "/backgrounds/pwk.jpg",
  "/backgrounds/tasik.jpg",
  "/backgrounds/serang.jpeg",
];

const BG_INTERVAL_MS = 9 * 60 * 1000;

export default function AdminIngestPage() {
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);

  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(DEFAULT_CATEGORIES[0]);
  const [customCategory, setCustomCategory] = useState("");
  const [chunkSize, setChunkSize] = useState("");
  const [overlap, setOverlap] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const category = selectedCategory === CUSTOM_CATEGORY_KEY ? customCategory.trim() : selectedCategory;

  const handleSubmit = useCallback(async () => {
    if (!file || !token || !category) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const cs = chunkSize ? parseInt(chunkSize, 10) : undefined;
      const ov = overlap ? parseInt(overlap, 10) : undefined;
      if (cs !== undefined && (isNaN(cs) || cs < 100 || cs > 2000)) {
        setError("Ukuran chunk harus antara 100–2000 karakter.");
        setLoading(false);
        return;
      }
      if (ov !== undefined && (isNaN(ov) || ov < 0 || ov > 5)) {
        setError("Overlap harus antara 0–5 kalimat.");
        setLoading(false);
        return;
      }
      const res = await api.ingestPdf(token, file, category, title || undefined, cs, ov);
      setResult(
        `${res.message}${res.chunks_added != null ? ` (${res.chunks_added} potongan ditambahkan)` : ""}`,
      );
      setFile(null);
      setTitle("");
      if (fileRef.current) fileRef.current.value = "";
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal mengunggah file.");
    } finally {
      setLoading(false);
    }
  }, [file, token, category, title, chunkSize, overlap]);

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

  return (
    <Shell>
      <div className="mx-auto w-full max-w-lg space-y-6">
        <div className="flex items-center gap-4">
          <img
            src="/add-pdf-icon.png"
            alt="Tambah Dokumen"
            className="h-12 w-12 object-contain"
          />
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Tambah Dokumen PDF</h2>
            <p className="text-sm text-muted-foreground">
              Unggah file PDF untuk ditambahkan ke basis pengetahuan chatbot.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              File PDF
            </label>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-primary/10 file:px-3 file:py-1 file:text-sm file:font-medium file:text-primary"
            />
            {file && (
              <p className="mt-1 text-xs text-muted-foreground">
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Judul Dokumen{" "}
              <span className="font-normal text-muted-foreground">(opsional)</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Kosongkan untuk menggunakan nama file"
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Kategori
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            >
              {DEFAULT_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
              <option value={CUSTOM_CATEGORY_KEY}>+ Kategori lainnya…</option>
            </select>

            {selectedCategory === CUSTOM_CATEGORY_KEY && (
              <div className="mt-2 flex items-center gap-2">
                <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                <input
                  type="text"
                  value={customCategory}
                  onChange={(e) => setCustomCategory(e.target.value)}
                  placeholder="Tulis nama kategori baru"
                  autoFocus
                  className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                />
              </div>
            )}
          </div>

          {/* Advanced: Chunk Settings */}
          <div className="rounded-md border border-border">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex w-full items-center justify-between px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Pengaturan Chunk (Lanjutan)</span>
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>

            {showAdvanced && (
              <div className="border-t border-border px-3 pb-3 pt-2 space-y-3">
                <p className="text-xs text-muted-foreground">
                  Atur bagaimana teks PDF dipotong menjadi potongan-potongan kecil (chunk) untuk pencarian.
                  Kosongkan untuk menggunakan nilai default.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="mb-1 block text-xs font-medium">
                      Ukuran Chunk
                      <span className="ml-1 font-normal text-muted-foreground">(karakter)</span>
                    </label>
                    <input
                      type="number"
                      value={chunkSize}
                      onChange={(e) => setChunkSize(e.target.value)}
                      placeholder="Auto (350/900)"
                      min={100}
                      max={2000}
                      className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium">
                      Overlap
                      <span className="ml-1 font-normal text-muted-foreground">(kalimat)</span>
                    </label>
                    <input
                      type="number"
                      value={overlap}
                      onChange={(e) => setOverlap(e.target.value)}
                      placeholder="Default (1)"
                      min={0}
                      max={5}
                      className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                    />
                  </div>
                </div>

                <div className="rounded bg-surface-muted px-3 py-2 text-xs text-muted-foreground space-y-1">
                  <p><strong>Default:</strong> Tabel → 350 karakter, teks biasa → 900 karakter, overlap 1 kalimat.</p>
                  <p><strong>Tip:</strong> Untuk PDF dengan banyak tabel/jadwal, gunakan chunk kecil (200–400). Untuk PDF narasi panjang, bisa lebih besar (800–1200).</p>
                </div>
              </div>
            )}
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!file || !category || loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Memproses…
              </>
            ) : (
              <>
                <img src="/add-pdf-icon.png" alt="" className="mr-2 h-4 w-4 object-contain" />
                Unggah & Proses
              </>
            )}
          </Button>

          {result && (
            <div className="flex items-start gap-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800 dark:border-green-800 dark:bg-green-950 dark:text-green-200">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{result}</span>
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-200">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Panduan Upload PDF */}
        <div className="rounded-md border border-border">
          <button
            type="button"
            onClick={() => setShowGuide(!showGuide)}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <Info className="h-4 w-4" />
            <span>Panduan Upload PDF</span>
            {showGuide ? <ChevronUp className="ml-auto h-4 w-4" /> : <ChevronDown className="ml-auto h-4 w-4" />}
          </button>

          {showGuide && (
            <div className="border-t border-border px-4 pb-4 pt-3 text-sm text-muted-foreground space-y-4">
              <section>
                <h4 className="font-semibold text-foreground mb-1">Jenis Dokumen yang Didukung</h4>
                <ul className="list-disc ml-4 space-y-0.5">
                  <li>PDF dengan teks biasa (surat, pengumuman, panduan)</li>
                  <li>PDF dengan tabel (kalender akademik, jadwal, daftar biaya)</li>
                  <li>PDF hasil scan akan di-OCR otomatis (perlu Tesseract terinstal)</li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Tips Agar Tabel Ter-extract dengan Baik</h4>
                <ul className="list-disc ml-4 space-y-0.5">
                  <li>Tabel dalam PDF akan otomatis dikonversi ke kalimat terstruktur</li>
                  <li>Untuk PDF yang <strong>didominasi tabel</strong> (jadwal, kalender), gunakan
                    ukuran chunk kecil (<strong>200–400 karakter</strong>) agar setiap jadwal menjadi
                    chunk terpisah dan lebih mudah ditemukan chatbot</li>
                  <li>Untuk PDF <strong>narasi panjang</strong> (panduan, peraturan), biarkan default
                    atau gunakan chunk lebih besar (<strong>800–1200 karakter</strong>)</li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Kapan Perlu Atur Chunk Manual?</h4>
                <ul className="list-disc ml-4 space-y-0.5">
                  <li><strong>Chatbot tidak bisa menjawab</strong> pertanyaan dari PDF baru →
                    coba upload ulang dengan chunk lebih kecil (300–400)</li>
                  <li><strong>Jawaban terpotong</strong> atau konteksnya kurang →
                    perbesar chunk (1000–1500) dan/atau naikkan overlap ke 2–3</li>
                  <li><strong>PDF berisi banyak tabel kecil</strong> (jadwal per baris) →
                    chunk 200–350, overlap 0</li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Pengaturan Overlap</h4>
                <p>
                  Overlap menambahkan kalimat terakhir dari chunk sebelumnya ke awal chunk berikutnya,
                  agar konteks tidak hilang di perbatasan chunk.
                </p>
                <ul className="list-disc ml-4 space-y-0.5">
                  <li><strong>0</strong> — Tanpa overlap. Cocok untuk tabel/jadwal yang tiap baris independen</li>
                  <li><strong>1</strong> (default) — Satu kalimat overlap. Cukup untuk kebanyakan dokumen</li>
                  <li><strong>2–3</strong> — Lebih banyak konteks. Untuk narasi panjang yang saling terhubung</li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Menghindari Masalah Umum</h4>
                <ol className="list-decimal ml-4 space-y-1">
                  <li>
                    <strong>Upload ulang PDF yang sama:</strong> Sistem otomatis mengganti chunk lama
                    jika path file sama. Jika perlu memperbarui konten, upload ulang dari halaman ini.
                  </li>
                  <li>
                    <strong>Judul dokumen penting:</strong> Judul yang deskriptif
                    (mis. &ldquo;Kalender Akademik UPI 2026/2027&rdquo;) membantu chatbot menemukan
                    chunk yang relevan. Hindari judul generik seperti &ldquo;Dokumen&rdquo;.
                  </li>
                  <li>
                    <strong>Kategori yang tepat:</strong> Gunakan kategori yang konsisten.
                    Kategori membantu pengguna mengetahui asal sumber jawaban.
                  </li>
                </ol>
              </section>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const [bgIndex, setBgIndex] = useState(
    () => Math.floor(Math.random() * BG_IMAGES.length),
  );
  const [nextIndex, setNextIndex] = useState<number | null>(null);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const id = setInterval(() => {
      const next = (bgIndex + 1) % BG_IMAGES.length;
      setNextIndex(next);
      setFading(true);
      const fadeTimer = setTimeout(() => {
        setBgIndex(next);
        setNextIndex(null);
        setFading(false);
      }, 1500);
      return () => clearTimeout(fadeTimer);
    }, BG_INTERVAL_MS);
    return () => clearInterval(id);
  }, [bgIndex]);

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-start px-4 pt-16">
      {/* Background photo layer */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-[1500ms]"
        style={{
          backgroundImage: `url(${BG_IMAGES[bgIndex]})`,
          opacity: fading ? 0 : 1,
        }}
      />
      {nextIndex !== null && (
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-[1500ms]"
          style={{
            backgroundImage: `url(${BG_IMAGES[nextIndex]})`,
            opacity: fading ? 1 : 0,
          }}
        />
      )}

      {/* Noise texture overlay (CSS-generated, no external image) */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`,
          mixBlendMode: "multiply",
        }}
      />

      {/* Semi-transparent overlay for readability */}
      <div className="pointer-events-none absolute inset-0 bg-background/75 dark:bg-background/85" />

      {/* Content */}
      <div className="relative z-10 mb-6 w-full max-w-lg">
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-1">
            <ArrowLeft className="h-4 w-4" />
            Kembali
          </Button>
        </Link>
      </div>
      <div className="relative z-10">{children}</div>
    </div>
  );
}
