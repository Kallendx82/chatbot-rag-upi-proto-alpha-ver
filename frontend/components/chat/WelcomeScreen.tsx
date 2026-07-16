"use client";

import { motion } from "framer-motion";

import { BrandLogo } from "@/components/ui/BrandLogo";
import { useI18n } from "@/contexts/I18nContext";

// Dashboard sengaja dibiarkan bersih (tanpa rekomendasi pertanyaan).
// `onPick` dipertahankan agar pemanggil (ChatPanel) tetap kompatibel.
export function WelcomeScreen(_props: { onPick: (prompt: string) => void }) {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col items-center text-center"
      >
          <div className="flex h-24 w-24 items-center justify-center rounded-lg bg-cyan text-primary-foreground">            
          <BrandLogo className="h-24 w-24" iconClassName="h-8 w-8" />
        </div>
        <h1 className="font-serif text-3xl font-semibold tracking-tight">
          {t("common.appName")}
        </h1>
        <p className="mt-1 text-xs font-medium text-muted-foreground">
          {t("common.subtitle")}
        </p>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          {t("welcome.description")}
        </p>
      </motion.div>
    </div>
  );
}
