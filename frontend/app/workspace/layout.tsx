"use client";

import { ReactNode } from "react";
import { SessionGate } from "@/lib/session";
import { Shell, NavItem } from "@/components/Shell";
import { IconChat, IconDashboard, IconDocument, IconGear, IconInbox } from "@/components/Icons";

const NAV: NavItem[] = [
  { href: "/workspace", label: "Overview", icon: <IconDashboard /> },
  { href: "/workspace/documents", label: "Documents", icon: <IconDocument /> },
  { href: "/workspace/chats", label: "Chats", icon: <IconChat /> },
  { href: "/workspace/requests", label: "Requests", icon: <IconInbox /> },
  { href: "/workspace/settings", label: "Settings", icon: <IconGear /> },
];

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <SessionGate area="workspace">
      <Shell nav={NAV}>{children}</Shell>
    </SessionGate>
  );
}
