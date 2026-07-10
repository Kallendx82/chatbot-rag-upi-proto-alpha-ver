"use client";

import { useState } from "react";
import Link from "next/link";
import { BarChart3, ChevronDown, LogIn, LogOut, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuDivider,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  const [open, setOpen] = useState(false);

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
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 border border-white/25 bg-white/10 px-3 text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:border-border dark:bg-surface dark:text-foreground dark:hover:bg-surface-muted"
        >
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[11px] font-semibold text-accent-foreground">
            {user.username.slice(0, 1).toUpperCase()}
          </span>
          <span className="max-w-[8rem] truncate text-xs font-medium">
            {user.username}
          </span>
          <ChevronDown className="h-4 w-4 opacity-70" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuLabel className="text-center text-xs font-semibold text-muted-foreground">
          Akun
        </DropdownMenuLabel>
        <DropdownMenuDivider />

        {user.is_admin && (
          <>
            <DropdownMenuItem asChild>
              <Link
                href="/stats"
                className="flex items-center gap-2 cursor-pointer"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Statistik penggunaan</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuDivider />
          </>
        )}

        <DropdownMenuItem
          onClick={() => {
            setOpen(false);
            setAuthModalOpen(true);
          }}
          className="flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground"
        >
          <UserPlus className="h-4 w-4" />
          <span>Ganti ke akun lain</span>
        </DropdownMenuItem>

        <DropdownMenuDivider />

        <DropdownMenuItem
          onClick={() => {
            setOpen(false);
            void logout();
          }}
          className="flex items-center gap-2 cursor-pointer text-destructive hover:text-destructive hover:bg-destructive/10"
        >
          <LogOut className="h-4 w-4" />
          <span>Keluar</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
