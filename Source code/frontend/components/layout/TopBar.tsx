"use client";

import { Bug, PanelLeft } from "lucide-react";

import { UserMenu } from "@/components/auth/UserMenu";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useHealth, type ConnectionState } from "@/hooks/useHealth";
import { useUIStore } from "@/store/settingsStore";
import { useI18n } from "@/contexts/I18nContext";
import { cn } from "@/lib/utils";

export function TopBar() {
  const { t } = useI18n();
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const setDebugPanelOpen = useUIStore((s) => s.setDebugPanelOpen);
  const { state } = useHealth();

  const STATUS_META: Record<
    ConnectionState,
    { label: string; dot: string; text: string }
  > = {
    checking: { label: "Checking…", dot: "bg-muted-foreground", text: "text-muted-foreground" },
    online: { label: t("header.connected"), dot: "bg-teal", text: "text-teal" },
    degraded: { label: "Pipeline not ready", dot: "bg-accent", text: "text-accent-foreground" },
    offline: { label: t("header.disconnected"), dot: "bg-destructive", text: "text-destructive" },
  };
  const meta = STATUS_META[state];

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b-2 border-accent bg-primary px-3 dark:border-b dark:border-border dark:bg-surface/80 dark:backdrop-blur">
      <div className="flex items-center gap-2">
        {!sidebarOpen && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={toggleSidebar}
                aria-label={t("sidebar.closeSidebar")}
                className="text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:text-foreground dark:hover:bg-surface-muted"
              >
                <PanelLeft className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>{t("sidebar.closeSidebar")}</TooltipContent>
          </Tooltip>
        )}
        <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1">
          <span className={cn("h-2 w-2 rounded-full", meta.dot)} />
          <span className={cn("text-xs font-medium", meta.text)}>
            {meta.label}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDebugPanelOpen(true)}
              className="gap-2 border-white/30 bg-transparent text-primary-foreground hover:bg-white/15 hover:text-primary-foreground dark:border-teal/40 dark:bg-surface dark:text-teal dark:hover:bg-teal/10"
            >
              <Bug className="h-4 w-4" />
              <span className="hidden sm:inline">{t("header.retrievalDebug")}</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>{t("header.retrievalDebug")}</TooltipContent>
        </Tooltip>
        <UserMenu />
      </div>
    </header>
  );
}
