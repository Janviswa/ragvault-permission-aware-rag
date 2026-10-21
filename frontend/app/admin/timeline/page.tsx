"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useLoad } from "@/lib/hooks";
import { ActivityCategory, CATEGORY_LABELS, describeLog, Fact, logFacts } from "@/lib/activity";
import { dayLabel, formatTime } from "@/lib/format";
import type { AdminUser, AuditLog, DocumentItem } from "@/lib/types";
import { Empty, Loading, Notice, PageHeader } from "@/components/ui";
import { IconChevronDown, IconRefresh } from "@/components/Icons";

type Data = { logs: AuditLog[]; users: AdminUser[]; docs: DocumentItem[] };

const CATEGORY_COLORS: Record<ActivityCategory, string> = {
  questions: "#8da2f0",
  documents: "#a8dcea",
  permissions: "#b9a8ee",
  people: "#f4e58c",
  security: "#f5b5c0",
};

function FactRow({ fact }: { fact: Fact }) {
  return (
    <div className="grid grid-cols-[96px_1fr] gap-x-3 gap-y-1 py-1.5 text-[13px]">
      <dt className="text-ash">{fact.label}</dt>
      <dd className="min-w-0 break-words">
        {fact.chips ? (
          <span className="flex flex-wrap gap-1.5">
            {fact.chips.map((chip) => <span key={chip} className={fact.tone === "bad" ? "chip-strike" : "chip-sky"}>{chip}</span>)}
          </span>
        ) : (
          <span className={`${fact.tone === "bad" ? "font-semibold text-[#8a1c2f] dark:text-[#ffb3c1]" : fact.tone === "ok" ? "font-semibold text-[#11613a] dark:text-[#9be8bf]" : ""} ${fact.label === "Event" ? "font-mono text-[12px]" : ""}`}>{fact.value}</span>
        )}
      </dd>
    </div>
  );
}

export default function AdminTimeline() {
  const { data, error, loading, reload } = useLoad<Data>(async () => {
    const [logs, users, docs] = await Promise.all([
      apiRequest<AuditLog[]>("/admin/audit"),
      apiRequest<AdminUser[]>("/admin/users"),
      apiRequest<DocumentItem[]>("/documents"),
    ]);
    return { logs, users, docs };
  });
  const [person, setPerson] = useState("");
  const [category, setCategory] = useState<"" | ActivityCategory>("");
  const [openId, setOpenId] = useState<number | null>(null);
  const [replay, setReplay] = useState(0); // bump to replay the entrance animation

  // /admin/timeline?person=3 opens pre-filtered (used by the "View their activity" link on alerts)
  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("person");
    if (id) setPerson(id);
  }, []);

  const days = useMemo(() => {
    if (!data) return [];
    const ctx = {
      users: new Map(data.users.map((u) => [u.id, u.full_name] as [number, string])),
      docs: new Map(data.docs.map((d) => [d.id, d.title] as [number, string])),
    };
    const groups: { label: string; items: { log: AuditLog; who: string; what: string; failed: boolean; category: ActivityCategory; facts: Fact[] }[] }[] = [];
    for (const log of data.logs) {
      if (person && String(log.user_id) !== person) continue;
      const a = describeLog(log, ctx);
      if (category && a.category !== category) continue;
      const label = dayLabel(log.created_at);
      let group = groups[groups.length - 1];
      if (!group || group.label !== label) groups.push((group = { label, items: [] }));
      group.items.push({ log, who: a.who, what: a.what, failed: a.failed, category: a.category, facts: logFacts(log, ctx) });
    }
    return groups;
  }, [data, person, category]);

  const newestId = days[0]?.items[0]?.log.id;
  let index = 0; // running index across day groups for the stagger

  return (
    <>
      <PageHeader
        title="Timeline"
        subtitle="Who accessed what, and when. Click an event for the details. Shows the most recent 200 events."
        actions={<button className="btn-line" onClick={() => { setReplay((n) => n + 1); reload(); }}><IconRefresh size={15} /> Refresh</button>}
      />
      {error && <Notice kind="error">{error}</Notice>}

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div><label className="label" htmlFor="tl-person">Person</label>
          <select id="tl-person" className="field w-auto min-w-[200px]" value={person} onChange={(e) => { setPerson(e.target.value); setReplay((n) => n + 1); }}>
            <option value="">Everyone</option>{data?.users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
          </select></div>
        <div><label className="label" htmlFor="tl-cat">Type</label>
          <select id="tl-cat" className="field w-auto min-w-[160px]" value={category} onChange={(e) => { setCategory(e.target.value as "" | ActivityCategory); setReplay((n) => n + 1); }}>
            <option value="">All activity</option>{(Object.keys(CATEGORY_LABELS) as ActivityCategory[]).map((k) => <option key={k} value={k}>{CATEGORY_LABELS[k]}</option>)}
          </select></div>
        <ul className="ml-auto flex flex-wrap gap-x-4 gap-y-1 pb-2 text-[12px] text-ash" aria-label="Legend">
          {(Object.keys(CATEGORY_LABELS) as ActivityCategory[]).map((k) => (
            <li key={k} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: CATEGORY_COLORS[k] }} />{CATEGORY_LABELS[k]}</li>
          ))}
        </ul>
      </div>

      {loading && !data ? <div className="panel"><Loading /></div> : days.length === 0 ? (
        <div className="panel"><Empty title="No matching activity">{person || category ? "Try a different person or type." : "Activity will appear here as people use RAGVault."}</Empty></div>
      ) : (
        <div key={replay} className="space-y-6">
          {days.map((day) => (
            <section key={day.label} aria-label={day.label}>
              <h2 className="sticky top-0 z-10 mb-2 inline-block rounded-full bg-white/70 px-3 py-1 text-[13px] font-bold backdrop-blur-md">{day.label}</h2>
              <div className="relative ml-3 pl-7">
                <span aria-hidden="true" className="absolute bottom-2 left-0 top-1 w-[2px] origin-top animate-draw-line rounded-full bg-gradient-to-b from-periwinkle via-lavender to-transparent" />
                <ol className="space-y-2">
                  {day.items.map(({ log, who, what, failed, category: cat, facts }) => {
                    const i = index++;
                    const open = openId === log.id;
                    const color = failed ? "#e0556f" : CATEGORY_COLORS[cat];
                    return (
                      <li key={log.id} className="relative animate-fade-up" style={{ animationDelay: `${Math.min(i, 14) * 50}ms` }}>
                        <span aria-hidden="true" className="absolute -left-[35px] top-[18px] flex h-4 w-4 items-center justify-center">
                          {log.id === newestId && <span className="absolute inset-0 animate-ping-soft rounded-full" style={{ background: color }} />}
                          <span className={`relative h-3 w-3 rounded-full ring-4 ring-white transition-transform duration-300 ${open ? "scale-150" : ""}`} style={{ background: color }} />
                        </span>

                        <div className={`card transition-shadow duration-300 ${open ? "shadow-soft" : ""}`}>
                          <button
                            onClick={() => setOpenId(open ? null : log.id)}
                            aria-expanded={open}
                            aria-controls={`tl-${log.id}`}
                            className="flex w-full items-start gap-3 rounded-2xl px-4 py-3 text-left transition-colors hover:bg-white/60"
                          >
                            <span className="min-w-0 flex-1">
                              <span className="block text-sm leading-relaxed"><span className="font-semibold">{who}</span> {what}{failed && <span className="chip-strike ml-2">Failed</span>}</span>
                              <span className="block text-[12px] text-ash">{formatTime(log.created_at)} · {CATEGORY_LABELS[cat]}</span>
                            </span>
                            <IconChevronDown size={18} className={`mt-1 shrink-0 text-ash transition-transform duration-300 ${open ? "rotate-180" : ""}`} />
                          </button>

                          <div id={`tl-${log.id}`} aria-hidden={!open} className={`grid transition-all duration-300 ease-out ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
                            <div className="overflow-hidden">
                              <dl className="mx-4 mb-3 border-t border-fog pt-2">
                                {facts.map((fact, f) => (
                                  <div key={fact.label} className={open ? "animate-fade-up" : ""} style={{ animationDelay: `${f * 40}ms` }}>
                                    <FactRow fact={fact} />
                                  </div>
                                ))}
                              </dl>
                            </div>
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ol>
              </div>
            </section>
          ))}
        </div>
      )}
    </>
  );
}
