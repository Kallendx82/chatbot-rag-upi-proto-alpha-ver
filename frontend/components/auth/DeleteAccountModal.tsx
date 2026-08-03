import React, { useEffect, useState } from "react";
import { AlertTriangle, Eye, EyeOff, UserX } from "lucide-react";

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
import { ApiError } from "@/types";

export function DeleteAccountModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const deleteAccount = useAuthStore((s) => s.deleteAccount);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Math challenge state
  const [num1, setNum1] = useState(0);
  const [num2, setNum2] = useState(0);
  const [mathAnswer, setMathAnswer] = useState("");

  const generateCaptcha = () => {
    setNum1(Math.floor(Math.random() * 9) + 1); // 1-9
    setNum2(Math.floor(Math.random() * 9) + 1); // 1-9
    setMathAnswer("");
  };

  useEffect(() => {
    if (open) {
      generateCaptcha();
    }
  }, [open]);

  const reset = () => {
    setPassword("");
    setMathAnswer("");
    setError(null);
    setLoading(false);
  };

  const close = (o: boolean) => {
    onOpenChange(o);
    if (!o) reset();
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!password.trim()) {
      setError("Masukkan password Anda untuk konfirmasi.");
      return;
    }

    const calculated = num1 + num2;
    if (parseInt(mathAnswer.trim(), 10) !== calculated) {
      setError("Hasil penjumlahan salah. Silakan coba lagi.");
      generateCaptcha();
      return;
    }

    setLoading(true);
    try {
      await deleteAccount(password);
      close(false);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Gagal menghapus akun. Coba lagi.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="max-w-sm border-destructive/30">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <UserX className="h-5 w-5" />
            Hapus Akun Permanen
          </DialogTitle>
          <DialogDescription className="text-xs pt-1">
            Tindakan ini tidak dapat dibatalkan. Seluruh data akun dan riwayat chat Anda akan dihapus secara permanen dari server.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4 pt-2">
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 border border-destructive/20 p-2.5 text-xs text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="del-password" className="text-xs font-medium">
              Konfirmasi Password
            </Label>
            <div className="relative">
              <Input
                id="del-password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password Anda"
                disabled={loading}
                className="pr-10 text-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
            <Label htmlFor="del-captcha" className="text-xs font-medium text-destructive">
              Keamanan Tambahan: Berapa {num1} + {num2}?
            </Label>
            <Input
              id="del-captcha"
              type="text"
              value={mathAnswer}
              onChange={(e) => setMathAnswer(e.target.value)}
              placeholder="Masukkan hasil penjumlahan"
              disabled={loading}
              className="text-sm font-mono"
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => close(false)}
              disabled={loading}
            >
              Batal
            </Button>
            <Button
              type="submit"
              variant="destructive"
              size="sm"
              disabled={loading || !mathAnswer}
            >
              {loading ? "Menghapus..." : "Hapus Akun Saya"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
