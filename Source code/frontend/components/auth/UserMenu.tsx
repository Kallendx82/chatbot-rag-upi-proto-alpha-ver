"use client";

import Link from "next/link";
import { BarChart3, LogIn, LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuthStore } from "@/store/authStore";
import { useUIStore } from "@/store/settingsStore";

/**
 * Compact auth controls for the top bar. Logged out: a "Masuk" button that
 * opens the auth dialog. Logged in: username chip + stats shortcut (admin
 * only) + logout. Styled for the maroon header in light mode.
 */
export function UserMenu() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const setAuthModalOpen = useUIStore((s) => s.setAuthModalOpen);

  if (!user) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setAuthModalOpen(true)}
        className="gap-2 border-white/30 bg-transparent text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:border-border dark:bg-surface dark:text-foreground dark:hover:bg-surface-muted"
      >
        <LogIn className="h-4 w-4" />
        <span className="hidden sm:inline">Masuk</span>
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-1.5">
      <div className="flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-3 py-1 dark:border-border dark:bg-surface">
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[11px] font-semibold text-accent-foreground">
          {user.username.slice(0, 1).toUpperCase()}
        </span>
        <span className="max-w-[9rem] truncate text-xs font-medium text-primary-foreground dark:text-foreground">
          {user.username}
        </span>
      </div>

      {user.is_admin && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon-sm"
              asChild
              className="text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:text-foreground dark:hover:bg-surface-muted"
            >
              <Link href="/stats" aria-label="Statistik pertanyaan">
                <BarChart3 className="h-4 w-4" />
              </Link>
            </Button>
          </TooltipTrigger>
          <TooltipContent>Statistik pertanyaan (admin)</TooltipContent>
        </Tooltip>
      )}

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => void logout()}
            aria-label="Keluar"
            className="text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:text-foreground dark:hover:bg-surface-muted"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Keluar</TooltipContent>
      </Tooltip>
    </div>
  );
}
