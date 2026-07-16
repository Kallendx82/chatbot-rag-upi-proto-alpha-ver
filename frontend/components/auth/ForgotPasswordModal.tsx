"use client";

import { useState } from "react";
import { Eye, EyeOff, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/types";
import { api } from "@/services/api";

type Step = "email" | "reset";

export function ForgotPasswordModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const reset = () => {
    setStep("email");
    setEmail("");
    setToken("");
    setNewPassword("");
    setConfirm("");
    setError(null);
    setSuccess(false);
  };

  const close = (o: boolean) => {
    onOpenChange(o);
    if (!o) reset();
  };

  const requestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.forgotPassword(email);
      setToken(result.token);
      setStep("reset");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Terjadi kesalahan. Coba lagi.",
      );
    } finally {
      setLoading(false);
    }
  };

  const submitReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!token.trim()) {
      setError("Token harus diisi.");
      return;
    }

    if (!newPassword.trim()) {
      setError("Password baru harus diisi.");
      return;
    }

    if (newPassword !== confirm) {
      setError("Konfirmasi password tidak sama.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password minimal 8 karakter.");
      return;
    }

    setLoading(true);
    try {
      await api.resetPassword(token, newPassword);
      setSuccess(true);
      setTimeout(() => close(false), 2000);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Token tidak valid atau kedaluwarsa.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            Lupa Password
          </DialogTitle>
          <DialogDescription>
            {step === "email"
              ? "Masukkan email untuk menerima link reset password."
              : "Masukkan token dan password baru Anda."}
          </DialogDescription>
        </DialogHeader>

        {success ? (
          <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-center">
            <p className="text-sm font-medium text-green-900">
              ✓ Password berhasil direset! Silakan login dengan password baru.
            </p>
          </div>
        ) : step === "email" ? (
          <form onSubmit={requestReset} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="reset-email">Email</Label>
              <Input
                id="reset-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
                placeholder="nama@example.com"
              />
            </div>

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => close(false)}
                disabled={loading}
              >
                Batal
              </Button>
              <Button type="submit" className="flex-1" disabled={loading}>
                {loading ? "Mengirim…" : "Kirim Token Reset"}
              </Button>
            </div>
          </form>
        ) : (
          <form onSubmit={submitReset} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="reset-token">Reset Token</Label>
              <Input
                id="reset-token"
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
                placeholder="Paste token dari email"
                className="font-mono text-xs"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="reset-password">Password Baru</Label>
              <div className="relative">
                <Input
                  id="reset-password"
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  className="pr-10"
                  placeholder="Min. 8 karakter"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                  aria-label={showPassword ? "Sembunyikan" : "Tampilkan"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="reset-confirm">Ulangi Password Baru</Label>
              <div className="relative">
                <Input
                  id="reset-confirm"
                  type={showConfirm ? "text" : "password"}
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={8}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                  aria-label={showConfirm ? "Sembunyikan" : "Tampilkan"}
                >
                  {showConfirm ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={() => setStep("email")}
                disabled={loading}
              >
                Kembali
              </Button>
              <Button type="submit" className="flex-1" disabled={loading}>
                {loading ? "Menyimpan…" : "Reset Password"}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
