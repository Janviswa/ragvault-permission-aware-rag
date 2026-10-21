"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { ATTEMPT_TYPES, documentIdFromEvent, eventInfo, eventLabel } from "@/lib/activity";
import { formatDateTime, parseDate } from "@/lib/format";
import type { AdminUser, DocumentItem, LeakageResult, SecurityEvent, TemporaryAccess } from "@/lib/types";
import { ClassificationChip, Empty, Loading, Notice, PageHeader, SeverityChip } from "@/components/ui";
import { IconAlert, IconCheck, IconChevronDown } from "@/components/Icons";

type Data = { events: SecurityEvent[]; users: AdminUser[]; docs: DocumentItem[]; temps: TemporaryAccess[] };
type Tab = "alerts" | "attempts" | "temporary" | "leakage";

export default function AdminSecurity() {
  const { data, error, loading, reload } = useLoad<Data>(async () => {
    const [events, users, docs, temps] = await Promise.all([
      apiRequest<SecurityEvent[]>("/admin/security/events"),
      apiRequest<AdminUser[]>("/admin/users"),
      apiRequest<DocumentItem[]>("/documents"),
      apiRequest<TemporaryAccess[]>("/admin/security/temporary-access"),
    ]);
    return { events, users, docs, temps };
  });
  const [tab, setTab] = useState<Tab>("alerts");
  const [openId, setOpenId] = useState<number | null>(null);
  const test = useAction();
  const [result, setResult] = useState<LeakageResult | null>(null);

  // Opening this page marks everything as seen (the sidebar number drops to 0), but we remember
  // which events were new on arrival so they can still be pointed out during this visit.
  const [newIds, setNewIds] = useState<Set<number>>(new Set());
  const sentRef = useRef<Set<number>>(new Set());
  useEffect(() => {
    if (!data) return;
    const fresh = data.events.filter((e) => e.status === "open" && !sentRef.current.has(e.id)).map((e) => e.id);
    if (fresh.length === 0) return;
    fresh.forEach((id) => sentRef.current.add(id));
    setNewIds((current) => new Set([...Array.from(current), ...fresh]));
    apiRequest("/admin/security/events/acknowledge", { method: "POST" })
      .then(() => window.dispatchEvent(new Event("ragvault:badges")))
      .catch(() => undefined); // the page still works; the badge just updates next time
  }, [data]);

  const alerts = data?.events.filter((e) => e.severity === "high" || e.severity === "critical") ?? [];
  const attempts = data?.events.filter((e) => ATTEMPT_TYPES.has(e.event_type)) ?? [];
  const person = (id: number | null) => (id == null ? undefined : data?.users.find((u) => u.id === id));
  const personName = (id: number | null) => (id == null ? "System" : person(id)?.full_name ?? `User #${id}`);
  const doc = (id?: number) => (id == null ? undefined : data?.docs.find((d) => d.id === id));
  const newIn = (list: SecurityEvent[]) => list.filter((e) => newIds.has(e.id)).length;

  async function runTest() {
    const ok = await test.run(async () => { setResult(await apiRequest<LeakageResult>("/admin/security/leakage-test", { method: "POST" })); });
    if (ok) await reload();
  }

  const tabs: [Tab, string, number][] = [
    ["alerts", `Alerts (${alerts.length})`, newIn(alerts)],
    ["attempts", `Unauthorized attempts (${attempts.length})`, newIn(attempts)],
    ["temporary", `Temporary access (${data?.temps.length ?? 0})`, 0],
    ["leakage", "Leakage test", 0],
  ];

  const eventList = (items: SecurityEvent[], empty: string) => items.length === 0 ? <Empty title={empty} /> : (
    <ul>{items.map((e) => {
      const open = openId === e.id;
      const who = person(e.user_id);
      const d = doc(documentIdFromEvent(e.details));
      const info = eventInfo(e.event_type);
      const isNew = newIds.has(e.id);
      return (
        <li key={e.id} className="row">
          <h3>
            <button
              onClick={() => setOpenId(open ? null : e.id)}
              aria-expanded={open}
              aria-controls={`ev-${e.id}`}
              className={`flex w-full items-start gap-3 px-5 py-4 text-left transition-colors hover:bg-white/60 ${isNew && !open ? "bg-periwinkle/10" : ""}`}
            >
              <span className="min-w-0 flex-1">
                <span className="block text-sm"><span className="font-semibold">{personName(e.user_id)}</span> · {eventLabel(e.event_type)}</span>
                {d && <span className="mt-0.5 block text-sm text-graphite">Document: {d.title}</span>}
                {!d && e.details && <span className="mt-0.5 block break-words text-sm text-graphite">{e.details}</span>}
                <span className="mt-1 block text-[13px] text-ash">{formatDateTime(e.created_at)}</span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                {isNew && <span className="chip-solid">New</span>}
                <SeverityChip severity={e.severity} />
                <IconChevronDown size={18} className={`text-ash transition-transform duration-300 ${open ? "rotate-180" : ""}`} />
              </span>
            </button>
          </h3>

          <div id={`ev-${e.id}`} aria-hidden={!open} className={`grid transition-all duration-300 ease-out ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
            <div className="overflow-hidden">
              <div className="mx-5 mb-4 rounded-xl border border-line bg-white/50 p-4">
                <p className="text-sm font-bold">{info.title}</p>
                <dl className="mt-3 grid gap-x-8 gap-y-2 text-[13px] sm:grid-cols-2">
                  <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Person</dt><dd className="min-w-0 break-words">{who ? <>{who.full_name} <span className="text-ash">· {who.role}</span><span className="block text-ash">{who.email}</span></> : personName(e.user_id)}</dd></div>
                  <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">When</dt><dd>{parseDate(e.created_at).toLocaleString(undefined, { dateStyle: "full", timeStyle: "medium" })}</dd></div>
                  <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Severity</dt><dd><SeverityChip severity={e.severity} /></dd></div>
                  <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Status</dt><dd>{isNew ? "New — marked as seen when you opened this page" : "Seen"}</dd></div>
                  {d && <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Document</dt><dd className="min-w-0"><span className="mr-2 break-words">{d.title}</span><ClassificationChip value={d.classification} /></dd></div>}
                  <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Event</dt><dd className="font-mono text-[12px]">{e.event_type}</dd></div>
                  {e.details && <div className="flex gap-2 sm:col-span-2"><dt className="w-20 shrink-0 text-ash">Details</dt><dd className="min-w-0 break-words">{e.details}</dd></div>}
                </dl>

                <div className="mt-4 space-y-3 border-t border-fog pt-3 text-sm leading-relaxed">
                  <div><p className="text-[12px] font-bold uppercase tracking-wider text-ash">What this means</p><p className="mt-1">{info.meaning}</p></div>
                  <div><p className="text-[12px] font-bold uppercase tracking-wider text-ash">Suggested action</p><p className="mt-1">{info.action}</p></div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {who && <Link href={`/admin/timeline?person=${who.id}`} className="btn-line btn-sm">View their activity</Link>}
                  {d && <Link href="/admin/documents" className="btn-line btn-sm">Manage documents</Link>}
                  {who && <Link href="/admin/users" className="btn-line btn-sm">Manage {who.full_name.split(" ")[0]}&apos;s account</Link>}
                </div>
              </div>
            </div>
          </div>
        </li>
      );
    })}</ul>
  );

  const totalNew = newIds.size;

  return (
    <>
      <PageHeader
        title="Security"
        subtitle={totalNew ? `${totalNew} new since your last visit. Select an alert for the details.` : "Unauthorized attempts, leakage tests and alerts. Select an alert for the details."}
      />
      {error && <Notice kind="error">{error}</Notice>}

      <div role="tablist" aria-label="Security views" className="mb-4 flex flex-wrap gap-2">
        {tabs.map(([key, label, fresh]) => (
          <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={tab === key ? "tab tab-on" : "tab"}>
            {label}{fresh > 0 && <span className={`ml-2 rounded-full px-1.5 py-0.5 text-[11px] font-bold ${tab === key ? "bg-white/25" : "bg-periwinkle-deep text-onaccent"}`}>{fresh} new</span>}
          </button>
        ))}
      </div>

      <section className="panel overflow-hidden" role="tabpanel">
        {loading && !data ? <Loading /> : tab === "alerts" ? eventList(alerts, "No high-severity alerts")
          : tab === "attempts" ? eventList(attempts, "No unauthorized attempts")
          : tab === "temporary" ? ((data?.temps.length ?? 0) === 0 ? <Empty title="No active temporary access">Grants made from a document's Manage panel, or by approving a request for a set time, appear here until they expire.</Empty> : (
            <ul>{data!.temps.map((t) => (
              <li key={t.id} className="row flex flex-wrap justify-between gap-3 px-5 py-4 text-sm">
                <span><span className="font-semibold">{personName(t.user_id)}</span> can read <b>{t.document_title}</b></span>
                <span className="text-[13px] text-ash">until {formatDateTime(t.expires_at)}</span>
              </li>))}</ul>
          )) : (
            <div className="px-5 py-5">
              <p className="max-w-prose text-sm leading-relaxed text-graphite">Searches as each non-admin person, using the title of every document they can't read, and checks that none of those documents come back. It tests the search filter that protects the document index.</p>
              <button className="btn-solid mt-4" disabled={test.busy} onClick={runTest}>{test.busy ? "Running…" : "Run leakage test"}</button>
              {test.error && <div className="mt-4"><Notice kind="error" onDismiss={test.clear}>{test.error}</Notice></div>}
              {result && (
                <div className={`mt-5 rounded-2xl border p-4 ${result.passed ? "note-success" : "note-error"}`} role="status">
                  <p className="flex items-center gap-2 text-base font-semibold">{result.passed ? <><IconCheck size={18} /> Passed — nothing leaked</> : <><IconAlert size={18} /> Failed — {result.leaks.length} unauthorized result{result.leaks.length === 1 ? "" : "s"}</>}</p>
                  <p className="mt-1 text-sm opacity-90">{result.probes} searches across {result.users_tested} {result.users_tested === 1 ? "person" : "people"} · {formatDateTime(result.ran_at)}</p>
                  {result.capped && <p className="mt-1 text-sm">Stopped at the search limit; some combinations weren't tested.</p>}
                  {result.leaks.length > 0 && <ul className="mt-3 space-y-1 text-sm">{result.leaks.map((l, i) => <li key={i}>{personName(l.user_id)} received “{doc(l.document_id)?.title ?? `document #${l.document_id}`}”</li>)}</ul>}
                </div>
              )}
            </div>
          )}
      </section>
    </>
  );
}
