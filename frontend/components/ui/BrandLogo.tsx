"use client";

import { useState } from "react";
import { GraduationCap } from "lucide-react";

import { cn } from "@/lib/utils";

/**
 * Chatbot brand logo, swappable without touching code:
 * put your image at `frontend/public/logo.png` and it is used everywhere
 * this component renders (welcome screen, sidebar, bot avatar). When the
 * file does not exist, it falls back to the graduation-cap icon.
 *
 * A square PNG with transparent background (≥256×256 px) looks best.
 */
export function BrandLogo({
  className,
  iconClassName,
}: {
  /** Classes for the <img> variant (sizing). */
  className?: string;
  /** Classes for the fallback icon variant (sizing). */
  iconClassName?: string;
}) {
  const [missing, setMissing] = useState(false);

  if (missing) {
    return <GraduationCap className={cn(iconClassName ?? "h-4 w-4")} />;
  }
  // eslint-disable-next-line @next/next/no-img-element -- static public asset,
  // no next/image optimisation needed and onError must work reliably.
  return (
    <img
      src="/logo.png"
      alt="Logo chatbot"
      draggable={false}
      className={cn("object-contain select-none", className)}
      onError={() => setMissing(true)}
    />
  );
}
