"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { BarChart3, ChevronDown, Key, LogIn, LogOut, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/settingsStore";
import { useI18n } from "@/contexts/I18nContext";
import { ChangePasswordModal } from "@/components/auth/ChangePasswordModal";

/**
 * Compact auth controls for the top bar. Logged out: a "Masuk" button that
 * opens the auth dialog. Logged in: username chip + stats shortcut (admin
 * only) + logout. Styled for the maroon header in light mode.
 */
export function UserMenu() {
  const { t } = useI18n();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const setAuthModalOpen = useUIStore((s) => s.setAuthModalOpen);
  const [open, setOpen] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [open]);

  if (!user) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setAuthModalOpen(true)}
        className="gap-2 border-white/30 bg-transparent text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:border-border dark:bg-surface dark:text-foreground dark:hover:bg-surface-muted"
      >
        <LogIn className="h-4 w-4" />
        <span className="hidden sm:inline">{t("auth.login")}</span>
      </Button>
    );
  }

  return (
    <div ref={menuRef} className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen(!open)}
        className="gap-2 border border-white/25 bg-white/10 px-3 text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:border-border dark:bg-surface dark:text-foreground dark:hover:bg-surface-muted"
      >
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan text-[11px] font-semibold text-accent-foreground">
          {user.username.slice(0, 1).toUpperCase()}
        </span>
        <span className="max-w-[8rem] truncate text-xs font-medium">
          {user.username}
        </span>
        <ChevronDown className={`h-4 w-4 opacity-70 transition-transform ${open ? "rotate-180" : ""}`} />
      </Button>

      {open && (
        <div className="absolute right-0 mt-1 w-48 rounded-lg border border-border bg-surface shadow-lg z-50">
          <div className="px-3 py-2 text-center text-xs font-semibold text-muted-foreground border-b border-border">
            {t("user.account")}
          </div>

          {user.is_admin && (
            <>
              <Link
                href="/stats"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-muted cursor-pointer transition-colors"
              >
                <BarChart3 className="h-4 w-4" />
                <span>{t("user.usageStatistics")}</span>
              </Link>
              <Link
                href="/admin"
                onClick={() => setOpen(false)}
                className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-muted cursor-pointer transition-colors"
              >
                <img src="/add-pdf-icon.png" alt="Tambah Dokumen" className="h-4 w-4 object-contain" />
                <span>Tambah Dokumen</span>
              </Link>
              <div className="border-t border-border" />
            </>
          )}

          <button
            onClick={() => {
              setOpen(false);
              setShowChangePassword(true);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-surface-muted transition-colors text-left"
          >
            <Key className="h-4 w-4" />
            <span>{t("user.changePassword")}</span>
          </button>

          <button
            onClick={() => {
              setOpen(false);
              setAuthModalOpen(true);
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-surface-muted transition-colors text-left"
          >
            <UserPlus className="h-4 w-4" />
            <span>{t("user.switchAccount")}</span>
          </button>

          <div className="border-t border-border" />

          <button
            onClick={() => {
              setOpen(false);
              void logout();
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-destructive hover:text-destructive hover:bg-destructive/10 transition-colors text-left"
          >
            <LogOut className="h-4 w-4" />
            <span>{t("user.logout")}</span>
          </button>
        </div>
      )}

      <ChangePasswordModal
        open={showChangePassword}
        onOpenChange={setShowChangePassword}
      />
    </div>
  );
}
