"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Plus,
  Minus,
  ChevronDown,
  ChevronUp,
  Info,
  Trash2,
  FileText,
  RefreshCw,
  Search,
  Filter,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/services/api";
import { useAuthStore } from "@/store/authStore";
import { useMounted } from "@/hooks/useMounted";
import { LoadingScreen } from "@/components/ui/LoadingScreen";
import { cn } from "@/lib/utils";

const INITIAL_DEFAULT_CATEGORIES = [
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

const STORAGE_KEY = "upi-rag-all-categories";
const VISIBLE_WITHOUT_SCROLL = 6;

const DEFAULT_BG_FALLBACK = [
  "/backgrounds/background-1.jpg",
  "/backgrounds/background-2.jpg",
  "/backgrounds/sumedang.jpg",
  "/backgrounds/pwk.jpg",
  "/backgrounds/tasik.jpg",
  "/backgrounds/serang.jpeg",
];

const BG_INTERVAL_MS = 9 * 60 * 1000;

function loadCategories(): string[] {
  if (typeof window === "undefined") return INITIAL_DEFAULT_CATEGORIES;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return INITIAL_DEFAULT_CATEGORIES;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((s: unknown) => typeof s === "string" && (s as string).trim()) : INITIAL_DEFAULT_CATEGORIES;
  } catch {
    return INITIAL_DEFAULT_CATEGORIES;
  }
}

function saveCategories(cats: string[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cats));
}

interface IngestedDoc {
  doc_id: string;
  title: string;
  category?: string;
  subcategory?: string;
  chunks_count: number;
  created_at?: string;
}

export default function AdminIngestPage() {
  const mounted = useMounted();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);

  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");

  // --- category state ---
  const [categories, setCategories] = useState<string[]>(INITIAL_DEFAULT_CATEGORIES);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [newCategoryInput, setNewCategoryInput] = useState("");
  const [showNewInput, setShowNewInput] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // --- ingested documents state ---
  const [documents, setDocuments] = useState<IngestedDoc[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);
  const [docConfirmDelete, setDocConfirmDelete] = useState<string | null>(null);

  // --- filter & sort state for document list ---
  const [searchDocQuery, setSearchDocQuery] = useState("");
  const [filterDocCategory, setFilterDocCategory] = useState("ALL");
  const [sortDocOrder, setSortDocOrder] = useState<"newest" | "oldest" | "title_asc" | "chunks_desc">("newest");

  useEffect(() => {
    const loaded = loadCategories();
    setCategories(loaded);
    if (loaded.length > 0) {
      setSelectedCategory(loaded[0]);
    }
  }, []);

  const fetchDocuments = useCallback(async () => {
    if (!token) return;
    setLoadingDocs(true);
    try {
      const docs = await api.listDocuments(token);
      setDocuments(docs);
    } catch {
      // ignore
    } finally {
      setLoadingDocs(false);
    }
  }, [token]);

  useEffect(() => {
    if (mounted && token && user?.is_admin) {
      fetchDocuments();
    }
  }, [mounted, token, user, fetchDocuments]);

  // Filter & sort documents
  const filteredDocuments = useMemo(() => {
    let result = [...documents];

    // Search by title/name
    if (searchDocQuery.trim()) {
      const q = searchDocQuery.toLowerCase().trim();
      result = result.filter(
        (d) => d.title.toLowerCase().includes(q) || d.doc_id.toLowerCase().includes(q)
      );
    }

    // Filter by category
    if (filterDocCategory !== "ALL") {
      result = result.filter((d) => (d.category || "Uncategorized") === filterDocCategory);
    }

    // Sort
    result.sort((a, b) => {
      if (sortDocOrder === "title_asc") {
        return a.title.localeCompare(b.title);
      }
      if (sortDocOrder === "chunks_desc") {
        return b.chunks_count - a.chunks_count;
      }
      if (sortDocOrder === "oldest") {
        return (a.created_at || "").localeCompare(b.created_at || "");
      }
      // default: newest
      return (b.created_at || "").localeCompare(a.created_at || "");
    });

    return result;
  }, [documents, searchDocQuery, filterDocCategory, sortDocOrder]);

  // Unique categories existing in documents
  const existingDocCategories = useMemo(() => {
    const set = new Set<string>();
    for (const d of documents) {
      if (d.category) set.add(d.category);
    }
    return Array.from(set);
  }, [documents]);

  const needsScroll = categories.length > VISIBLE_WITHOUT_SCROLL;

  const addCategory = () => {
    const name = newCategoryInput.trim();
    if (!name) return;
    if (categories.includes(name)) {
      setSelectedCategory(name);
      setShowNewInput(false);
      setNewCategoryInput("");
      return;
    }
    const updated = [...categories, name];
    setCategories(updated);
    saveCategories(updated);
    setSelectedCategory(name);
    setShowNewInput(false);
    setNewCategoryInput("");
  };

  const deleteCategory = (cat: string) => {
    const updated = categories.filter((c) => c !== cat);
    setCategories(updated);
    saveCategories(updated);
    if (selectedCategory === cat) {
      setSelectedCategory(updated[0] || "");
    }
    setDeleteConfirm(null);
  };

  // --- math CAPTCHA validation for delete ---
  const [captchaNum1, setCaptchaNum1] = useState(0);
  const [captchaNum2, setCaptchaNum2] = useState(0);
  const [userAnswer, setUserAnswer] = useState("");
  const [captchaError, setCaptchaError] = useState(false);

  const initCaptcha = () => {
    setCaptchaNum1(Math.floor(Math.random() * 9) + 1); // 1-9
    setCaptchaNum2(Math.floor(Math.random() * 9) + 1); // 1-9
    setUserAnswer("");
    setCaptchaError(false);
  };

  const startConfirmDelete = (docId: string) => {
    initCaptcha();
    setDocConfirmDelete(docId);
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!token) return;
    const answer = parseInt(userAnswer.trim(), 10);
    if (isNaN(answer) || answer !== (captchaNum1 + captchaNum2)) {
      setCaptchaError(true);
      return;
    }
    setDeletingDocId(docId);
    try {
      await api.deleteDocument(token, docId);
      setResult(`Berhasil menghapus dokumen '${docId}' beserta chunk-nya.`);
      fetchDocuments();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal menghapus dokumen.");
    } finally {
      setDeletingDocId(null);
      setDocConfirmDelete(null);
      setUserAnswer("");
      setCaptchaError(false);
    }
  };

  // --- chunk / upload state ---
  const [subcategory, setSubcategory] = useState("");
  const [chunkSize, setChunkSize] = useState("");
  const [overlap, setOverlap] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateAndSetFile = (f: File | null) => {
    if (!f) {
      setFile(null);
      setError(null);
      return;
    }
    const isPdfExt = f.name.toLowerCase().endsWith(".pdf");
    const isPdfMime = f.type === "application/pdf" || f.type === "";
    if (!isPdfExt || !isPdfMime) {
      setFile(null);
      setError("Dokumen yang diunggah harus berformat .pdf! File yang Anda pilih terdeteksi bukan file .pdf. Silakan upload file PDF resmi.");
      if (fileRef.current) fileRef.current.value = "";
      return;
    }
    setError(null);
    setFile(f);
  };

  const [publishYear, setPublishYear] = useState("");

  const handleSubmit = useCallback(async () => {
    if (!file || !token || !selectedCategory) return;

    // Double check PDF format before submitting
    const isPdfExt = file.name.toLowerCase().endsWith(".pdf");
    const isPdfMime = file.type === "application/pdf" || file.type === "";
    if (!isPdfExt || !isPdfMime) {
      setError("Dokumen yang diunggah terdeteksi bukan file berformat .pdf! Mohon upload file PDF yang valid.");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const cs = chunkSize ? parseInt(chunkSize, 10) : undefined;
      const ov = overlap ? parseInt(overlap, 10) : undefined;
      const py = publishYear ? parseInt(publishYear, 10) : undefined;
      if (cs !== undefined && (isNaN(cs) || cs < 100 || cs > 2000)) {
        setError("Ukuran chunk harus antara 100–2000 karakter.");
        setLoading(false);
        return;
      }
      if (ov !== undefined && (isNaN(ov) || ov < 0 || ov > 500)) {
        setError("Overlap harus antara 0–500 karakter.");
        setLoading(false);
        return;
      }
      if (py !== undefined && (isNaN(py) || py < 1900 || py > 2100)) {
        setError("Tahun terbit harus berupa angka tahun yang valid (1900-2100).");
        setLoading(false);
        return;
      }
      const res = await api.ingestPdf(token, file, selectedCategory, subcategory || undefined, title || undefined, py, cs, ov);
      setResult(
        `${res.message}${res.chunks_added != null ? ` (${res.chunks_added} potongan ditambahkan)` : ""}`,
      );
      setFile(null);
      setTitle("");
      setSubcategory("");
      setPublishYear("");
      if (fileRef.current) fileRef.current.value = "";
      fetchDocuments();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Gagal mengunggah file. Pastikan file berformat .pdf yang valid.");
    } finally {
      setLoading(false);
    }
  }, [file, token, selectedCategory, subcategory, title, publishYear, chunkSize, overlap, fetchDocuments]);

  if (!mounted) return <LoadingScreen />;

  if (!user || !user.is_admin) {
    return (
      <Shell>
        <p className="text-sm text-muted-foreground">
          Halaman ini hanya untuk admin. Silakan masuk dengan akun admin terlebih dahulu.
        </p>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="mx-auto w-full max-w-lg space-y-6">
        <div className="flex items-center gap-4">
          <img src="/add-pdf-icon.png" alt="Tambah Dokumen" className="h-12 w-12 object-contain" />
          <div className="space-y-1">
            <h2 className="text-lg font-semibold">Kelola & Tambah Dokumen PDF</h2>
            <p className="text-sm text-muted-foreground">
              Unggah atau hapus dokumen PDF &amp; chunk dari basis pengetahuan chatbot.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {/* File input */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">File PDF</label>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={(e) => validateAndSetFile(e.target.files?.[0] ?? null)}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-primary/10 file:px-3 file:py-1 file:text-sm file:font-medium file:text-primary"
            />
            {file && (
              <p className="mt-1 text-xs text-muted-foreground">
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Title */}
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

          {/* Category selector */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">Kategori</label>
            <div
              className={`rounded-md border border-border bg-background ${needsScroll ? "max-h-52 overflow-y-auto" : ""}`}
            >
              {categories.length === 0 ? (
                <div className="px-3 py-3 text-xs text-muted-foreground text-center">
                  Belum ada kategori. Tambahkan kategori baru di bawah.
                </div>
              ) : (
                categories.map((cat) => {
                  const isSelected = selectedCategory === cat;
                  return (
                    <div
                      key={cat}
                      className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors text-sm ${
                        isSelected ? "bg-primary/10 text-primary font-medium" : "hover:bg-surface-muted text-foreground"
                      }`}
                      onClick={() => setSelectedCategory(cat)}
                    >
                      <span className="truncate flex-1">{cat}</span>
                      {deleteConfirm === cat ? (
                        <div
                          className="flex items-center gap-1.5 ml-2 shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <span className="text-xs text-destructive">Hapus?</span>
                          <button
                            onClick={() => deleteCategory(cat)}
                            className="rounded px-2 py-0.5 text-xs font-medium bg-destructive text-destructive-foreground hover:bg-destructive/80"
                          >
                            Ya
                          </button>
                          <button
                            onClick={() => setDeleteConfirm(null)}
                            className="rounded px-2 py-0.5 text-xs font-medium bg-muted text-muted-foreground hover:bg-muted/80"
                          >
                            Batal
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={(e) => { e.stopPropagation(); setDeleteConfirm(cat); }}
                          title={`Hapus kategori "${cat}"`}
                          className="ml-2 shrink-0 flex h-5 w-5 items-center justify-center rounded hover:bg-destructive/15 text-muted-foreground hover:text-destructive transition-colors"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  );
                })
              )}
            </div>

            {showNewInput ? (
              <div className="mt-2 flex items-center gap-2">
                <Plus className="h-4 w-4 shrink-0 text-muted-foreground" />
                <input
                  type="text"
                  value={newCategoryInput}
                  onChange={(e) => setNewCategoryInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") addCategory();
                    if (e.key === "Escape") { setShowNewInput(false); setNewCategoryInput(""); }
                  }}
                  placeholder="Tulis nama kategori baru, lalu Enter"
                  autoFocus
                  className="block flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                />
                <button
                  onClick={addCategory}
                  disabled={!newCategoryInput.trim()}
                  className="rounded-md bg-primary px-3 py-2 text-xs font-medium text-primary-foreground disabled:opacity-50 hover:bg-primary/90 transition-colors"
                >
                  Tambah
                </button>
                <button
                  onClick={() => { setShowNewInput(false); setNewCategoryInput(""); }}
                  className="rounded-md border border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-surface-muted transition-colors"
                >
                  Batal
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowNewInput(true)}
                className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                + Kategori lainnya…
              </button>
            )}
          </div>

          {/* Sub-category */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Sub-kategori{" "}
              <span className="font-normal text-muted-foreground">(opsional, mis. Kalender-Akademik-2026)</span>
            </label>
            <input
              type="text"
              value={subcategory}
              onChange={(e) => setSubcategory(e.target.value)}
              placeholder="Contoh: Kalender-Akademik-2026"
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
            />
          </div>

          {/* Tahun Akademik Dokumen/Informasi Terbit */}
          <div>
            <label className="mb-1.5 block text-sm font-medium">
              Tahun Akademik Dokumen/Informasi Terbit{" "} - Direkomendasikan untuk diisi
              <span className="font-normal text-muted-foreground">(opsional, mis. 2026)</span>
            </label>
            <input
              type="number"
              value={publishYear}
              onChange={(e) => setPublishYear(e.target.value)}
              placeholder="Contoh: 2026"
              min={1900}
              max={2100}
              className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
            />
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
                      placeholder="Auto (350/1000)"
                      min={100}
                      max={2000}
                      className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium">
                      Overlap
                      <span className="ml-1 font-normal text-muted-foreground">(karakter)</span>
                    </label>
                    <input
                      type="number"
                      value={overlap}
                      onChange={(e) => setOverlap(e.target.value)}
                      placeholder="Default (200)"
                      min={0}
                      max={500}
                      className="block w-full rounded-md border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground"
                    />
                  </div>
                </div>
                <div className="rounded bg-surface-muted px-3 py-2 text-xs text-muted-foreground space-y-1">
                  <p><strong>Default:</strong> Tabel → 350 karakter, teks biasa → 1000 karakter, overlap 200 karakter.</p>
                  <p><strong>Tip:</strong> PDF tabel/jadwal: chunk kecil (200–400). PDF narasi panjang: chunk lebih besar (800–1200). Setiap chunk otomatis diakhiri di titik atau baris baru.</p>
                </div>
              </div>
            )}
          </div>

          <Button onClick={handleSubmit} disabled={!file || !selectedCategory || loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Memproses…
              </>
            ) : (
              <>
                <img src="/add-pdf-icon.png" alt="" className="mr-2 h-4 w-4 object-contain" />
                Unggah &amp; Proses
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

        {/* Section: Daftar Dokumen & Filter/Urutkan/Hapus Chunk */}
        <div className="rounded-lg border border-border bg-background p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              <h3 className="text-sm font-semibold">
                Daftar Dokumen di Index ({filteredDocuments.length}/{documents.length})
              </h3>
            </div>
            <button
              onClick={fetchDocuments}
              disabled={loadingDocs}
              title="Refresh daftar dokumen"
              className="p-1 rounded text-muted-foreground hover:text-foreground hover:bg-surface-muted transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingDocs ? "animate-spin" : ""}`} />
            </button>
          </div>

          {/* Filter, Search & Sort Bar */}
          <div className="space-y-2 pt-1">
            {/* Search Input */}
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchDocQuery}
                onChange={(e) => setSearchDocQuery(e.target.value)}
                placeholder="Cari berdasarkan nama/judul dokumen..."
                className="w-full rounded-md border border-border bg-background pl-8 pr-3 py-1.5 text-xs placeholder:text-muted-foreground"
              />
            </div>

            {/* Category Filter & Sort Order Controls */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <select
                  value={filterDocCategory}
                  onChange={(e) => setFilterDocCategory(e.target.value)}
                  className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs"
                >
                  <option value="ALL">Semua Kategori</option>
                  {existingDocCategories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <select
                  value={sortDocOrder}
                  onChange={(e) => setSortDocOrder(e.target.value as any)}
                  className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs"
                >
                  <option value="newest">Terbaru</option>
                  <option value="oldest">Terlama</option>
                  <option value="title_asc">Nama (A-Z)</option>
                  <option value="chunks_desc">Chunk Terbanyak</option>
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {filteredDocuments.length === 0 ? (
              <p className="py-4 text-center text-xs text-muted-foreground">
                {loadingDocs ? "Memuat dokumen…" : "Tidak ada dokumen yang sesuai filter."}
              </p>
            ) : (
              filteredDocuments.map((doc) => {
                const isDeleting = deletingDocId === doc.doc_id;
                const isConfirming = docConfirmDelete === doc.doc_id;
                return (
                  <div
                    key={doc.doc_id}
                    className="flex items-center justify-between p-2.5 rounded-md border border-border bg-surface hover:border-primary/40 transition-colors gap-2"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium truncate text-foreground">{doc.title}</p>
                      <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-0.5">
                        {doc.category && (
                          <span className="rounded bg-surface-muted px-1.5 py-0.5 font-medium">
                            {doc.category}
                          </span>
                        )}
                        {doc.subcategory && (
                          <span className="rounded bg-primary/10 text-primary px-1.5 py-0.5 font-medium">
                            {doc.subcategory}
                          </span>
                        )}
                        <span>{doc.chunks_count} chunk</span>
                        {doc.created_at && (
                          <span className="font-mono text-[10px] text-muted-foreground/80">
                            ({doc.created_at})
                          </span>
                        )}
                      </div>
                    </div>

                    {isConfirming ? (
                      <div className="flex flex-col items-end gap-1 shrink-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-semibold text-destructive">
                            Berapa {captchaNum1} + {captchaNum2}?
                          </span>
                          <input
                            type="text"
                            value={userAnswer}
                            onChange={(e) => {
                              setUserAnswer(e.target.value);
                              setCaptchaError(false);
                            }}
                            placeholder="?"
                            className={cn(
                              "w-10 rounded border bg-background px-1.5 py-0.5 text-center text-xs font-mono",
                              captchaError ? "border-red-500 bg-red-50" : "border-border"
                            )}
                            style={{ width: "3rem" }}
                          />
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleDeleteDocument(doc.doc_id)}
                            disabled={isDeleting || !userAnswer}
                            className="rounded px-2 py-0.5 text-[11px] font-medium bg-destructive text-destructive-foreground hover:bg-destructive/80 disabled:opacity-50"
                          >
                            {isDeleting ? <Loader2 className="h-3 w-3 animate-spin" /> : "Hapus"}
                          </button>
                          <button
                            onClick={() => setDocConfirmDelete(null)}
                            disabled={isDeleting}
                            className="rounded px-2 py-0.5 text-[11px] font-medium bg-muted text-muted-foreground hover:bg-muted/80"
                          >
                            Batal
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => startConfirmDelete(doc.doc_id)}
                        disabled={isDeleting}
                        title={`Hapus dokumen "${doc.title}" dan seluruh chunk-nya`}
                        className="p-1.5 rounded text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors shrink-0"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Panduan Upload PDF */}
        <div className="rounded-md border border-border">
          <button
            type="button"
            onClick={() => setShowGuide(!showGuide)}
            className="flex w-full items-center gap-2 px-3 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <Info className="h-4 w-4" />
            <span>Panduan Upload &amp; Kelola Dokumen</span>
            {showGuide ? <ChevronUp className="ml-auto h-4 w-4" /> : <ChevronDown className="ml-auto h-4 w-4" />}
          </button>

          {showGuide && (
            <div className="border-t border-border px-4 pb-4 pt-3 text-sm text-muted-foreground space-y-4">
              <section>
                <h4 className="font-semibold text-foreground mb-1">Menghapus Dokumen &amp; Chunk</h4>
                <p>
                  Gunakan daftar <strong>Daftar Dokumen di Index</strong> untuk mencari, menyaring per kategori, mengurutkan berdasarkan nama/tanggal, dan menghapus dokumen yang tidak relevan. Menghapus dokumen akan menghapus seluruh chunk-nya dari FAISS vectorstore secara langsung tanpa merestart server.
                </p>
              </section>

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
                  <li>Untuk PDF yang <strong>didominasi tabel</strong> (jadwal, kalender), gunakan ukuran chunk kecil (<strong>200–400 karakter</strong>) agar setiap jadwal menjadi chunk terpisah</li>
                  <li>Untuk PDF <strong>narasi panjang</strong> (panduan, peraturan), biarkan default atau gunakan chunk lebih besar (<strong>800–1200 karakter</strong>)</li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Mencegah Dokumen Tidak Relevan &amp; Penamaan Judul/Kategori</h4>
                <ul className="list-disc ml-4 space-y-1">
                  <li>
                    <strong>Gunakan Judul Dokumen yang Jelas &amp; Deskriptif:</strong> Isi bidang <em>Judul Dokumen (opsional)</em> dengan nama yang jelas (contoh: <code>Pedoman Penulisan Karya Ilmiah UPI 2024</code> alih-alih <code>Doc1.pdf</code>). Judul dokumen ikut di-embed ke dalam pencarian sehingga menentukan relevansi hasil RAG.
                  </li>
                  <li>
                    <strong>Pilih / Buat Kategori Spesifik:</strong> Selalu tempatkan dokumen pada kategori yang tepat (misal: <em>Direktorat Pendidikan</em>, <em>PMB UPI</em>, dll). Jika dokumen berisi topik spesifik baru, Anda dapat menambahkan kategori/sub-kategori spesifik baru dengan mengklik <code>+ Kategori lainnya…</code>.
                  </li>
                  <li>
                    <strong>Periksa Relevansi di Retrieval Debug:</strong> Setelah meng-ingest dokumen baru, gunakan tombol <strong>Retrieval Debug</strong> di pojok kanan atas untuk mengetes pertanyaan uji dan memastikan chunk baru tersebut di-retrieve secara tepat pada topik yang relevan.
                  </li>
                </ul>
              </section>

              <section>
                <h4 className="font-semibold text-foreground mb-1">Pengaturan Overlap</h4>
                <p>Overlap menyalin sejumlah karakter terakhir dari chunk sebelumnya ke awal chunk berikutnya, agar konteks tidak hilang di perbatasan chunk.</p>
                <ul className="list-disc ml-4 space-y-0.5 mt-1">
                  <li><strong>0</strong> — Tanpa overlap. Cocok untuk tabel/jadwal yang tiap baris independen</li>
                  <li><strong>200</strong> (default) — ~200 karakter overlap. Cukup untuk kebanyakan dokumen</li>
                  <li><strong>300–400</strong> — Lebih banyak konteks. Untuk narasi panjang yang saling terhubung</li>
                </ul>
              </section>
            </div>
          )}
        </div>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const [bgList, setBgList] = useState<string[]>(DEFAULT_BG_FALLBACK);
  const [bgIndex, setBgIndex] = useState(0);
  const [nextIndex, setNextIndex] = useState<number | null>(null);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    fetch("/api/backgrounds")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setBgList(data);
          setBgIndex(Math.floor(Math.random() * data.length));
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (bgList.length <= 1) return;
    const id = setInterval(() => {
      const next = (bgIndex + 1) % bgList.length;
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
  }, [bgIndex, bgList]);

  const currentBg = bgList[bgIndex] || DEFAULT_BG_FALLBACK[0];
  const nextBg = nextIndex !== null ? bgList[nextIndex] : null;

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-start px-4 pt-16">
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-[1500ms]"
        style={{ backgroundImage: `url(${currentBg})`, opacity: fading ? 0 : 1 }}
      />
      {nextBg !== null && (
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-[1500ms]"
          style={{ backgroundImage: `url(${nextBg})`, opacity: fading ? 1 : 0 }}
        />
      )}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.08'/%3E%3C/svg%3E")`,
          mixBlendMode: "multiply",
        }}
      />
      <div className="pointer-events-none absolute inset-0 bg-background/75 dark:bg-background/85" />
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
