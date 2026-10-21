"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { API_URL, apiRequest } from "@/lib/api";
import { useLoad } from "@/lib/hooks";
import { describeLog } from "@/lib/activity";
import { formatDateTime, plural } from "@/lib/format";
import type { AnalyticsRange, AnalyticsSummary, AuditLog, AdminUser, DocumentItem, Health } from "@/lib/types";
import { Loading, Notice } from "@/components/ui";
import { ActivityPanel } from "@/components/ActivityPanel";
import { Stat } from "@/components/Stat";
import { IconAlert, IconCheck, IconDocument, IconInbox, IconRefresh, IconShield, IconChat, IconUsers } from "@/components/Icons";

type Overview = { logs: AuditLog[]; users: AdminUser[]; docs: DocumentItem[] };

const CLASS_COLORS: Record<string, string> = { Public: "#a8dcea", Internal: "#8da2f0", Confidential: "#b9a8ee", Restricted: "#f4e58c" };

function Bars({ items }: { items: [string, number][] }) {
  const max = Math.max(1, ...items.map(([, n]) => n));
  return (
    <ul className="space-y-4">
      {items.map(([label, n]) => (
        <li key={label}>
          <div className="mb-1.5 flex justify-between text-[13px]"><span className="font-medium">{label}</span><span className="text-graphite">{n}</span></div>
          <div className="h-1.5 rounded-full bg-white/80"><div className="h-1.5 rounded-full bg-gradient-to-r from-periwinkle to-lavender" style={{ width: `${(n / max) * 100}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}

function Donut({ counts }: { counts: Record<string, number> }) {
  const order = ["Public", "Internal", "Confidential", "Restricted"];
  const total = order.reduce((n, k) => n + (counts[k] ?? 0), 0);
  let acc = 0;
  const stops = order.filter((k) => (counts[k] ?? 0) > 0).map((k) => {
    const start = (acc / total) * 100;
    acc += counts[k];
    return `${CLASS_COLORS[k]} ${start}% ${(acc / total) * 100}%`;
  });
  return (
    <div>
      <div role="img" aria-label={`Documents by classification: ${order.map((k) => `${counts[k] ?? 0} ${k}`).join(", ")}`}
        className="relative mx-auto h-44 w-44 rounded-full shadow-lift" style={{ background: total ? `conic-gradient(${stops.join(", ")})` : "rgb(var(--c-fog))" }}>
        <div className="absolute inset-[26px] flex flex-col items-center justify-center rounded-full bg-white/90 shadow-inner">
          <span className="text-[32px] font-bold leading-none">{total}</span>
          <span className="mt-1 text-[12px] text-ash">Documents</span>
        </div>
      </div>
      <ul className="mt-5 space-y-2 text-[13px]">
        {order.map((k) => (
          <li key={k} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: CLASS_COLORS[k] }} />
            <span className="flex-1 truncate">{k}</span>
            <span className="text-graphite">{total ? Math.round(((counts[k] ?? 0) / total) * 100) : 0}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SystemStatus() {
  const [health, setHealth] = useState<Health | null>(null);
  const [checking, setChecking] = useState(true);
  const check = useCallback(async () => {
    setChecking(true);
    try {
      const response = await fetch(`${API_URL}/health`);
      setHealth(await response.json());
    } catch {
      setHealth({});
    } finally {
      setChecking(false);
    }
  }, []);
  useEffect(() => { check(); }, [check]);

  const rows: [string, string | undefined][] = [["API", health?.api], ["Database", health?.postgres], ["Document index", health?.qdrant]];
  return (
    <section className="panel flex min-h-0 flex-col overflow-hidden" aria-labelledby="sys-title">
      <div className="panel-head shrink-0">
        <h2 id="sys-title" className="text-[15px] font-bold">System status</h2>
        <button className="btn-quiet btn-sm" onClick={check} disabled={checking} aria-label="Check system status again"><IconRefresh size={15} className={checking ? "animate-spin" : ""} /></button>
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto px-5 py-2">
        {rows.map(([name, status]) => (
          <li key={name} className="row flex items-center justify-between py-3 text-sm">
            <span>{name}</span>
            {health === null ? <span className="text-ash">Checking…</span> : status === "ok"
              ? <span className="chip-good"><IconCheck size={12} /> Operational</span>
              : <span className="chip-strike"><IconAlert size={12} /> Unreachable</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function AdminDashboard() {
  const [range, setRange] = useState<AnalyticsRange>("7d");
  const summaryLoad = useLoad(() => apiRequest<AnalyticsSummary>(`/admin/analytics/summary?range=${range}`), [range]);
  const restLoad = useLoad<Overview>(async () => {
    const [logs, users, docs] = await Promise.all([
      apiRequest<AuditLog[]>("/admin/audit"),
      apiRequest<AdminUser[]>("/admin/users"),
      apiRequest<DocumentItem[]>("/documents"),
    ]);
    return { logs, users, docs };
  });

  const s = summaryLoad.data;
  const data = restLoad.data;
  const error = summaryLoad.error || restLoad.error;
  const ctx = data && {
    users: new Map(data.users.map((u) => [u.id, u.full_name] as [number, string])),
    docs: new Map(data.docs.map((d) => [d.id, d.title] as [number, string])),
  };

  return (
    <>
      <h1 className="sr-only">Dashboard</h1>
      {error && <Notice kind="error">{error}</Notice>}
      {(summaryLoad.loading && !s) && <div className="panel"><Loading /></div>}

      {s && ctx && data && (
        // min-h-full + a stretching last row: the cards end exactly where the sidebar ends
        <div className="flex min-h-full flex-col gap-4">
          <section aria-label="Totals" className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Stat label="People" value={s.totals.users} note={`${s.totals.active_users} active`} href="/admin/users" icon={<IconUsers size={16} />} tint="#cfd8fa" />
            <Stat label="Documents" value={s.totals.documents} note="Indexed" href="/admin/documents" icon={<IconDocument size={16} />} tint="#bfe6ef" />
            <Stat label="Pending requests" value={s.totals.pending_requests} note={s.totals.pending_requests ? "Waiting for you" : "All caught up"} href="/admin/requests" icon={<IconInbox size={16} />} tint="#f7eba4" />
            <Stat label="New security events" value={s.totals.open_security_events} note={s.totals.open_security_events ? "Not opened yet" : "All reviewed"} href="/admin/security" icon={<IconShield size={16} />} tint="#f7c9d1" />
            <Stat label="Questions today" value={s.today.queries} note={`${plural(s.today.document_views, "document")} opened`} icon={<IconChat size={16} />} tint="#ddd3f7" />
          </section>

          <div className="grid gap-4 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ActivityPanel
                title="Company activity"
                labels={{ a: "Questions asked", b: "Documents opened" }}
                data={s.activity}
                range={range}
                onRange={setRange}
                bucketDays={s.bucket_days}
                busy={summaryLoad.loading}
              />
            </div>
            <section className="panel" aria-labelledby="cls-title">
              <div className="panel-head"><h2 id="cls-title" className="text-[15px] font-bold">Documents by classification</h2></div>
              <div className="px-5 py-5"><Donut counts={s.documents_by_classification} /></div>
            </section>
          </div>

          {/* three equal cards; the row takes the remaining height, long content scrolls inside */}
          <div className="grid min-h-[340px] flex-1 grid-rows-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
            <section className="panel flex min-h-0 flex-col overflow-hidden" aria-labelledby="recent-title">
              <div className="panel-head shrink-0">
                <h2 id="recent-title" className="text-[15px] font-bold">Recent activity</h2>
                <Link href="/admin/timeline" className="text-[13px] font-semibold text-accent underline underline-offset-4">View all</Link>
              </div>
              {data.logs.length === 0 ? <p className="px-5 py-8 text-sm text-ash">Nothing has happened yet.</p> : (
                <ul className="min-h-0 flex-1 overflow-y-auto">
                  {data.logs.slice(0, 12).map((log) => {
                    const a = describeLog(log, ctx, true);
                    return (
                      <li key={log.id} className="row px-5 py-2.5 text-sm">
                        <p className="line-clamp-2 break-words"><span className="font-semibold">{a.who}</span> {a.what}</p>
                        <p className="text-[12px] text-ash">{formatDateTime(log.created_at)}</p>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>
            <section className="panel flex min-h-0 flex-col overflow-hidden" aria-labelledby="role-title">
              <div className="panel-head shrink-0"><h2 id="role-title" className="text-[15px] font-bold">People by role</h2></div>
              <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5"><Bars items={Object.entries(s.users_by_role)} /></div>
            </section>
            <SystemStatus />
          </div>
        </div>
      )}
    </>
  );
}
