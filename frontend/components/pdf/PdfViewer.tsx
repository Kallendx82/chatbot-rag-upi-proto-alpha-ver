"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, ExternalLink, FileText, Minus, Plus } from "lucide-react";
import { Document, Page, pdfjs } from "react-pdf";

import { Button } from "@/components/ui/button";

// NOTE: react-pdf/pdfjs-dist are pinned to exact versions in package.json
// (9.1.1 / 4.4.168). pdfjs-dist >= 4.7 crashes at import time under the
// webpack bundled with Next 14 ("Object.defineProperty called on non-object")
// — do not upgrade either package without also upgrading Next.
//
// The worker is served from /public (copied there by the predev/prebuild npm
// scripts) instead of being bundled: webpack's minifier cannot process the
// module-format worker file, and a local copy keeps the viewer working
// offline, e.g. during an on-campus demo without internet access.
// Served with a .js extension (same module-format file): .mjs is not in
// Cloudflare's default cacheable-extension list, .js is — so the 1.4 MB
// worker gets edge-cached instead of tunneling from the laptop every time.
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.js";

/**
 * In-app PDF viewer that reliably opens at the cited page.
 *
 * The browser's built-in viewer is not used because its handling of the
 * `#page=N` open-parameter varies per machine (and PDF-handling extensions
 * such as Adobe Acrobat ignore it entirely), which made citations open at
 * page 1. Rendering with pdf.js gives us full control over the initial page.
 */
export function PdfViewer({
  fileUrl,
  initialPage = 1,
  title,
}: {
  fileUrl: string;
  initialPage?: number;
  title?: string;
}) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(Math.max(1, initialPage));
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => setContainerWidth(el.clientWidth);
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const onLoad = useCallback(
    ({ numPages: n }: { numPages: number }) => {
      setNumPages(n);
      // Clamp the requested page into the document's real range.
      setPageNumber((p) => Math.min(Math.max(1, p), n));
    },
    [],
  );

  const goTo = (p: number) => {
    if (numPages == null) return;
    setPageNumber(Math.min(Math.max(1, p), numPages));
  };

  return (
    <div className="flex h-screen flex-col bg-surface-muted">
      <header className="flex items-center justify-between gap-3 border-b border-border bg-surface px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium">{title || "Dokumen sumber"}</span>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => goTo(pageNumber - 1)}
            disabled={pageNumber <= 1}
            aria-label="Halaman sebelumnya"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="whitespace-nowrap font-mono text-xs text-muted-foreground">
            <input
              type="number"
              value={pageNumber}
              min={1}
              max={numPages ?? 1}
              onChange={(e) => goTo(Number(e.target.value))}
              className="w-14 rounded border border-border bg-surface px-1.5 py-0.5 text-center text-xs"
              aria-label="Nomor halaman"
            />{" "}
            / {numPages ?? "…"}
          </span>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => goTo(pageNumber + 1)}
            disabled={numPages == null || pageNumber >= numPages}
            aria-label="Halaman berikutnya"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          <div className="mx-1 h-5 w-px bg-border" />

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)))}
            aria-label="Perkecil"
          >
            <Minus className="h-4 w-4" />
          </Button>
          <span className="w-10 text-center font-mono text-xs text-muted-foreground">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setZoom((z) => Math.min(3, +(z + 0.25).toFixed(2)))}
            aria-label="Perbesar"
          >
            <Plus className="h-4 w-4" />
          </Button>

          <div className="mx-1 h-5 w-px bg-border" />

          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => window.open(fileUrl, "_blank", "noopener,noreferrer")}
            aria-label="Buka berkas asli di tab baru"
            title="Buka berkas asli di tab baru"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <div ref={containerRef} className="flex-1 overflow-auto p-4 scrollbar-thin">
        {error ? (
          <div className="mx-auto mt-16 max-w-md rounded-lg border border-border bg-surface p-6 text-center text-sm text-muted-foreground">
            Gagal memuat PDF: {error}
          </div>
        ) : (
          <Document
            file={fileUrl}
            onLoadSuccess={onLoad}
            onLoadError={(e) => setError(e.message)}
            loading={
              <p className="mt-16 text-center text-sm text-muted-foreground">
                Memuat dokumen…
              </p>
            }
            className="flex justify-center"
          >
            <Page
              pageNumber={pageNumber}
              width={containerWidth ? Math.min(containerWidth - 32, 1000) * zoom : undefined}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              className="shadow-lg"
              loading={
                <p className="mt-16 text-center text-sm text-muted-foreground">
                  Merender halaman…
                </p>
              }
            />
          </Document>
        )}
      </div>
    </div>
  );
}

export default PdfViewer;
