"use client";

import Link from "next/link";
import { useState } from "react";
import { apiRequest } from "@/lib/api";
import { useLoad } from "@/lib/hooks";
import { formatDateTime, plural } from "@/lib/format";
import type { AnalyticsRange, ChatSummary, MyAnalytics } from "@/lib/types";
import { ActivityPanel } from "@/components/ActivityPanel";
import { useChat } from "@/components/ChatDock";
import { IconChat, IconDocument, IconInbox, IconNewChat } from "@/components/Icons";
import { Stat } from "@/components/Stat";
import { Loading, Notice } from "@/components/ui";

// What a non-admin sees: THEIR OWN activity. (Admins see the whole company on /admin.)
export default function WorkspaceOverview() {
  const { openChat } = useChat();
  const [range, setRange] = useState<AnalyticsRange>("7d");
  const mine = useLoad(() => apiRequest<MyAnalytics>(`/me/analytics?range=${range}`), [range]);
  const chats = useLoad(() => apiRequest<ChatSummary[]>("/chats"));

  const s = mine.data;
  const recent = (chats.data ?? []).slice(0, 5);

  return (
    <div className="flex min-h-full flex-col gap-4">
      <h1 className="sr-only">Overview</h1>
      {mine.error && <Notice kind="error">{mine.error}</Notice>}
      {!s && mine.loading && <div className="panel"><Loading /></div>}

      {s && (
        <>
          <section aria-label="Your totals" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat label="Documents you can open" value={s.totals.documents} note="Based on your role and grants" href="/workspace/documents" icon={<IconDocument size={16} />} tint="#bfe6ef" />
            <Stat label="Questions asked" value={s.totals.questions} note={`${plural(s.today.queries, "question")} today`} icon={<IconChat size={16} />} tint="#ddd3f7" />
            <Stat label="Saved chats" value={s.totals.chats} note="Only you can see them" href="/workspace/chats" icon={<IconNewChat size={16} />} tint="#cfd8fa" />
            <Stat label="Pending requests" value={s.totals.requests_pending} note={`${s.totals.requests_approved} approved · ${s.totals.requests_rejected} rejected`} href="/workspace/requests" icon={<IconInbox size={16} />} tint="#f7eba4" />
          </section>

          <ActivityPanel
            title="Your activity"
            labels={{ a: "Your questions", b: "Documents you opened" }}
            data={s.activity}
            range={range}
            onRange={setRange}
            bucketDays={s.bucket_days}
            busy={mine.loading}
          />

          <div className="grid min-h-[330px] flex-1 grid-rows-[minmax(0,1fr)] gap-4 lg:grid-cols-3">
            <section className="panel flex min-h-0 flex-col overflow-hidden lg:col-span-2" aria-labelledby="rc-title">
              <div className="panel-head shrink-0">
                <h2 id="rc-title" className="text-[15px] font-bold">Recent chats</h2>
                <Link href="/workspace/chats" className="text-[13px] font-semibold text-accent underline underline-offset-4">View all</Link>
              </div>
              {recent.length === 0 ? (
                <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 py-8 text-center">
                  <p className="text-sm text-graphite">No chats yet. Ask a question about your documents.</p>
                  <button className="btn-solid" onClick={() => openChat()}>Start a chat</button>
                </div>
              ) : (
                <ul className="min-h-0 flex-1 overflow-y-auto">
                  {recent.map((chat) => (
                    <li key={chat.id} className="row">
                      <button onClick={() => openChat(chat.id)} className="flex w-full items-center justify-between gap-4 px-5 py-3 text-left hover:bg-white/60">
                        <span className="min-w-0">
                          <span className="block truncate text-sm font-semibold">{chat.title}</span>
                          <span className="block text-[12px] text-ash">{formatDateTime(chat.updated_at)}</span>
                        </span>
                        <span className="shrink-0 text-[13px] font-semibold text-accent">Open</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="panel flex min-h-0 flex-col overflow-hidden" aria-labelledby="rq-title">
              <div className="panel-head shrink-0"><h2 id="rq-title" className="text-[15px] font-bold">Access requests</h2></div>
              <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-5 text-sm">
                <p className="flex items-center justify-between"><span className="chip-wait">Pending</span><span className="font-bold">{s.totals.requests_pending}</span></p>
                <p className="flex items-center justify-between"><span className="chip-good">Approved</span><span className="font-bold">{s.totals.requests_approved}</span></p>
                <p className="flex items-center justify-between"><span className="chip-strike">Rejected</span><span className="font-bold">{s.totals.requests_rejected}</span></p>
                <p className="pt-1 text-[13px] text-ash">When the assistant says a document is restricted, use “Request access” in the chat.</p>
                <Link href="/workspace/requests" className="btn-line btn-sm w-full justify-center">See all requests</Link>
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
