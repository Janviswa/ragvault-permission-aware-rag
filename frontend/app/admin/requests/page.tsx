"use client";

import { useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { formatDateTime, parseDate } from "@/lib/format";
import type { AdminAccessRequest } from "@/lib/types";
import { ClassificationChip, Empty, Loading, Notice, PageHeader, StatusChip } from "@/components/ui";

const TABS = [["pending", "Pending"], ["approved", "Approved"], ["rejected", "Rejected"], ["all", "All"]] as const;

// How long an approval lasts. "perm" keeps the old behaviour (permanent read access).
const OPTIONS = [
  { key: "perm", label: "Permanent", hours: 0 },
  { key: "1h", label: "1 hour", hours: 1 },
  { key: "1d", label: "1 day", hours: 24 },
  { key: "1w", label: "1 week", hours: 24 * 7 },
  { key: "custom", label: "Custom…", hours: 0 },
] as const;
type OptionKey = (typeof OPTIONS)[number]["key"];

function localInput(date: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function AdminRequests() {
  const [tab, setTab] = useState<(typeof TABS)[number][0]>("pending");
  const { data, error, loading, reload } = useLoad(() => apiRequest<AdminAccessRequest[]>(`/admin/access-requests?status=${tab}`), [tab]);
  const action = useAction();
  const [busyId, setBusyId] = useState<number | null>(null);
  const [choice, setChoice] = useState<Record<number, OptionKey>>({});
  const [custom, setCustom] = useState<Record<number, string>>({});
  const [formError, setFormError] = useState<Record<number, string>>({});

  const optionOf = (id: number): OptionKey => choice[id] ?? "perm";

  function endsAt(id: number): Date | null {
    const key = optionOf(id);
    if (key === "perm") return null;
    if (key === "custom") return custom[id] ? new Date(custom[id]) : null;
    return new Date(Date.now() + OPTIONS.find((o) => o.key === key)!.hours * 3_600_000);
  }

  async function approve(r: AdminAccessRequest) {
    const key = optionOf(r.id);
    let body: Record<string, unknown> | undefined;
    if (key === "custom") {
      const when = custom[r.id] ? new Date(custom[r.id]) : null;
      if (!when || Number.isNaN(when.getTime())) return setFormError((e) => ({ ...e, [r.id]: "Choose when the access should end." }));
      if (when.getTime() <= Date.now()) return setFormError((e) => ({ ...e, [r.id]: "That time has already passed." }));
      body = { expires_at: when.toISOString() };
    } else if (key !== "perm") {
      body = { duration_hours: OPTIONS.find((o) => o.key === key)!.hours };
    }
    setFormError((e) => ({ ...e, [r.id]: "" }));
    setBusyId(r.id);
    const ok = await action.run(async () => {
      const result = await apiRequest<{ expires_at: string | null }>(`/admin/access-requests/${r.id}/approve`, {
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
      return result.expires_at
        ? `${r.user_name} can read “${r.document_title}” until ${formatDateTime(result.expires_at)}.`
        : `${r.user_name} can now read “${r.document_title}”.`;
    });
    setBusyId(null);
    if (ok) await reload();
  }

  async function reject(r: AdminAccessRequest) {
    setBusyId(r.id);
    const ok = await action.run(async () => {
      await apiRequest(`/admin/access-requests/${r.id}/reject`, { method: "POST" });
      return `Request from ${r.user_name} was rejected.`;
    });
    setBusyId(null);
    if (ok) await reload();
  }

  return (
    <>
      <PageHeader title="Access requests" subtitle="Approve or reject requests to open restricted documents. Choose how long each approval lasts." />
      {error && <Notice kind="error">{error}</Notice>}
      {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
      {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}

      <div role="tablist" aria-label="Request status" className="mb-4 flex flex-wrap gap-2">
        {TABS.map(([key, label]) => (
          <button key={key} role="tab" aria-selected={tab === key} onClick={() => setTab(key)} className={tab === key ? "tab tab-on" : "tab"}>{label}</button>
        ))}
      </div>

      {loading ? <div className="panel"><Loading /></div> : (data?.length ?? 0) === 0 ? (
        <div className="panel"><Empty title={tab === "pending" ? "No pending requests" : "Nothing here"}>{tab === "pending" ? "You're all caught up." : "No requests with this status."}</Empty></div>
      ) : (
        <ul className="space-y-3">
          {data!.map((r) => {
            const end = endsAt(r.id);
            const expired = r.access_expires_at ? parseDate(r.access_expires_at).getTime() <= Date.now() : false;
            return (
              <li key={r.id} className="card p-4 sm:px-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[15px] font-semibold">{r.user_name} <span className="font-normal text-ash">· {r.user_role}</span></p>
                    <p className="mt-0.5 text-sm">wants to open <b>{r.document_title}</b></p>
                  </div>
                  <div className="flex items-center gap-2">
                    <ClassificationChip value={r.document_classification} />
                    {r.access_expires_at && <span className={expired ? "chip-soft" : "chip-sky"}>{expired ? "Expired" : "Temporary"}</span>}
                    <StatusChip status={r.status} />
                  </div>
                </div>
                <p className="mt-2 text-[13px] text-ash">
                  {r.user_email} · Requested {formatDateTime(r.requested_at)}
                  {r.decided_at ? ` · ${r.status === "approved" ? "Approved" : "Rejected"}${r.decided_by ? ` by ${r.decided_by}` : ""} ${formatDateTime(r.decided_at)}` : ""}
                  {r.access_expires_at ? ` · ${expired ? "ended" : "until"} ${formatDateTime(r.access_expires_at)}` : r.status === "approved" ? " · permanent access" : ""}
                </p>
                {r.reason && <p className="mt-2 rounded-lg bg-mist px-3 py-2 text-sm break-words">“{r.reason}”</p>}

                {r.status === "pending" && (
                  <div className="mt-4 rounded-xl border border-line bg-white/50 p-3.5">
                    <p className="label !mb-2" id={`dur-${r.id}`}>How long should the access last?</p>
                    <div role="radiogroup" aria-labelledby={`dur-${r.id}`} className="flex flex-wrap gap-2">
                      {OPTIONS.map((o) => (
                        <button
                          key={o.key}
                          role="radio"
                          aria-checked={optionOf(r.id) === o.key}
                          onClick={() => {
                            setChoice((c) => ({ ...c, [r.id]: o.key }));
                            if (o.key === "custom" && !custom[r.id]) setCustom((c) => ({ ...c, [r.id]: localInput(new Date(Date.now() + 24 * 3_600_000)) }));
                            setFormError((e) => ({ ...e, [r.id]: "" }));
                          }}
                          className={optionOf(r.id) === o.key ? "tab tab-on" : "tab"}
                        >
                          {o.label}
                        </button>
                      ))}
                    </div>
                    {optionOf(r.id) === "custom" && (
                      <div className="mt-3 max-w-xs">
                        <label className="label" htmlFor={`until-${r.id}`}>Ends at</label>
                        <input id={`until-${r.id}`} type="datetime-local" className="field" value={custom[r.id] ?? ""} onChange={(e) => setCustom((c) => ({ ...c, [r.id]: e.target.value }))} />
                      </div>
                    )}
                    <p className="hint mt-2.5" aria-live="polite">
                      {end
                        ? `Temporary: ${r.user_name.split(" ")[0]} can read it until ${formatDateTime(end.toISOString())}, then it stops on its own.`
                        : "Permanent: stays until you remove it under Documents → Manage."}
                    </p>
                    {formError[r.id] && <p role="alert" className="mt-2 text-[13px] font-semibold text-[#8a1c2f] dark:text-[#ffb3c1]">{formError[r.id]}</p>}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button className="btn-solid btn-sm" disabled={busyId === r.id} onClick={() => approve(r)}>
                        {optionOf(r.id) === "perm" ? "Approve" : `Approve for ${optionOf(r.id) === "custom" ? "a set time" : OPTIONS.find((o) => o.key === optionOf(r.id))!.label}`}
                      </button>
                      <button className="btn-line btn-sm" disabled={busyId === r.id} onClick={() => reject(r)}>Reject</button>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}
