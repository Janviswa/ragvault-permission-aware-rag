"use client";

import { ReactNode, useEffect } from "react";
import { usePathname } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { SessionGate } from "@/lib/session";
import { useLoad } from "@/lib/hooks";
import type { AnalyticsSummary } from "@/lib/types";
import { Shell, NavItem } from "@/components/Shell";
import { IconClock, IconDashboard, IconDocument, IconGear, IconInbox, IconShield, IconUsers } from "@/components/Icons";

function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  // Refresh the pending-request badge whenever the admin moves between pages.
  const { data, reload } = useLoad(() => apiRequest<AnalyticsSummary>("/admin/analytics/summary"), [pathname]);

  // The Security page announces when it has marked alerts as seen, so the badge drops right away.
  useEffect(() => {
    const refresh = () => { reload(); };
    window.addEventListener("ragvault:badges", refresh);
    return () => window.removeEventListener("ragvault:badges", refresh);
  }, [reload]);

  const nav: NavItem[] = [
    { href: "/admin", label: "Dashboard", icon: <IconDashboard /> },
    { href: "/admin/users", label: "Users & Roles", icon: <IconUsers /> },
    { href: "/admin/documents", label: "Documents", icon: <IconDocument /> },
    { href: "/admin/requests", label: "Access Requests", icon: <IconInbox />, badge: data?.totals.pending_requests },
    { href: "/admin/timeline", label: "Timeline", icon: <IconClock /> },
    { href: "/admin/security", label: "Security", icon: <IconShield />, badge: data?.totals.open_security_events },
    { href: "/admin/settings", label: "Settings", icon: <IconGear /> },
  ];
  return <Shell nav={nav}>{children}</Shell>;
}

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGate area="admin">
      <AdminShell>{children}</AdminShell>
    </SessionGate>
  );
}
