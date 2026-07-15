"use client";

import { useState } from "react";
import { Eye, EyeOff, KeyRound, LogIn, UserPlus } from "lucide-react";

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
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/settingsStore";
import { ApiError } from "@/types";
import { cn } from "@/lib/utils";

type Mode = "login" | "register";

const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])/;

function validatePassword(pwd: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (pwd.length < 8) errors.push("Minimal 8 karakter");
  if (!/[a-z]/.test(pwd)) errors.push("Minimal 1 huruf kecil");
  if (!/[A-Z]/.test(pwd)) errors.push("Minimal 1 huruf besar");
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd))
    errors.push("Minimal 1 karakter khusus (*, #, ^, &, dsb)");
  return { valid: errors.length === 0, errors };
}

/**
 * Login / sign-up dialog. Deliberately its own modal, separate from Settings:
 * auth is an identity concern, not an app preference.
 */
export function AuthModal() {
  const open = useUIStore((s) => s.authModalOpen);
  const setOpen = useUIStore((s) => s.setAuthModalOpen);
  const { login, register, busy } = useAuthStore();

  const [mode, setMode] = useState<Mode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const reset = () => {
    setEmail("");
    setPassword("");
    setConfirm("");
    setPasswordErrors([]);
    setError(null);
  };

  const close = (o: boolean) => {
    setOpen(o);
    if (!o) reset();
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPasswordErrors([]);

    if (mode === "register") {
      const { valid, errors } = validatePassword(password);
      if (!valid) {
        setPasswordErrors(errors);
        return;
      }
      if (!email.trim()) {
        setError("Email wajib diisi.");
        return;
      }
      if (password !== confirm) {
        setError("Konfirmasi password tidak sama.");
        return;
      }
    }

    try {
      if (mode === "login") await login(username.trim(), password);
      else await register(username.trim(), password, email.trim());
      close(false);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Terjadi kesalahan. Coba lagi.",
      );
    }
  };

  return (
    <>
      <Dialog open={open} onOpenChange={close}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-5 w-5 text-primary" />
              {mode === "login" ? "Masuk" : "Buat akun"}
            </DialogTitle>
            <DialogDescription>
              {mode === "login"
                ? "Masuk untuk menyimpan dan membuka riwayat percakapan Anda."
                : "Daftar untuk menyimpan riwayat percakapan Anda di akun."}
            </DialogDescription>
          </DialogHeader>

          {/* Mode switch */}
          <div className="grid grid-cols-2 gap-1 rounded-lg bg-surface-muted p-1">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => {
                  setMode(m);
                  setError(null);
                }}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  mode === m
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {m === "login" ? "Masuk" : "Daftar"}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="auth-username">Username</Label>
              <Input
                id="auth-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                minLength={3}
                maxLength={32}
              />
            </div>

            {mode === "register" && (
              <div className="space-y-1.5">
                <Label htmlFor="auth-email">Email</Label>
                <Input
                  id="auth-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                  placeholder="nama@example.com"
                />
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="auth-password">Password</Label>
              <div className="relative">
                <Input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (mode === "register") {
                      const { errors } = validatePassword(e.target.value);
                      setPasswordErrors(errors);
                    }
                  }}
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  required
                  minLength={mode === "register" ? 8 : 6}
                  maxLength={128}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                  aria-label={showPassword ? "Sembunyikan password" : "Tampilkan password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>

              {mode === "register" && passwordErrors.length > 0 && (
                <div className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive space-y-1">
                  {passwordErrors.map((err, i) => (
                    <div key={i}>• {err}</div>
                  ))}
                </div>
              )}
            </div>

            {mode === "register" && (
              <div className="space-y-1.5">
                <Label htmlFor="auth-confirm">Ulangi password</Label>
                <div className="relative">
                  <Input
                    id="auth-confirm"
                    type={showConfirm ? "text" : "password"}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    autoComplete="new-password"
                    required
                    minLength={8}
                    maxLength={128}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    tabIndex={-1}
                    aria-label={showConfirm ? "Sembunyikan password" : "Tampilkan password"}
                  >
                    {showConfirm ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            )}

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            {/* Forgot password disabled for alpha */}

            <Button type="submit" className="w-full gap-2" disabled={busy}>
              {mode === "login" ? (
                <LogIn className="h-4 w-4" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {busy
                ? "Memproses…"
                : mode === "login"
                  ? "Masuk"
                  : "Daftar & masuk"}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* ForgotPasswordModal disabled for alpha */}
    </>
  );
}
