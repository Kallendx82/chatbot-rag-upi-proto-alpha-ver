"use client";

import { Suspense } from "react";
import dynamic from "next/dynamic";
import { useSearchParams } from "next/navigation";

// pdf.js touches browser-only APIs (DOMMatrix, canvas), so the viewer must
// never be server-rendered.
const PdfViewer = dynamic(
  () => import("@/components/pdf/PdfViewer"),
  { ssr: false },
);

/** API base, mirroring services/api.ts (proxy in dev, env-driven in prod). */
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "/backend-api";

function ViewerInner() {
  const params = useSearchParams();
  const doc = params.get("doc") || "";
  const page = Number(params.get("page")) || 1;
  const title = params.get("title") || undefined;

  if (!doc) {
    return (
      <div className="flex h-screen items-center justify-center text-sm text-muted-foreground">
        Parameter dokumen tidak ditemukan.
      </div>
    );
  }

  const fileUrl = `${API_BASE}/api/source/${encodeURIComponent(doc)}.pdf`;
  return <PdfViewer fileUrl={fileUrl} initialPage={page} title={title} />;
}

export default function ViewerPage() {
  return (
    <Suspense fallback={null}>
      <ViewerInner />
    </Suspense>
  );
}
