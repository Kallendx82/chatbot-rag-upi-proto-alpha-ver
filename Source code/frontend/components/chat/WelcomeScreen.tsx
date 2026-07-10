"use client";

import { motion } from "framer-motion";

import { BrandLogo } from "@/components/ui/BrandLogo";

// Dashboard sengaja dibiarkan bersih (tanpa rekomendasi pertanyaan).
// `onPick` dipertahankan agar pemanggil (ChatPanel) tetap kompatibel.
export function WelcomeScreen(_props: { onPick: (prompt: string) => void }) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col items-center text-center"
      >
        <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
          <BrandLogo className="h-12 w-12" iconClassName="h-8 w-8" />
        </div>
        <h1 className="font-serif text-3xl font-semibold tracking-tight">
          Asisten Informasi UPI
        </h1>
        <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
          Tanyakan informasi seputar Universitas Pendidikan Indonesia. Setiap
          jawaban didukung sumber dokumen resmi yang dapat Anda telusuri.
        </p>
      </motion.div>
    </div>
  );
}
