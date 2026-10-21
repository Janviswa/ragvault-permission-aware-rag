"use client";

import { useState } from "react";
import { apiRequest } from "@/lib/api";
import { useLoad } from "@/lib/hooks";
import { formatDateTime, parseDate } from "@/lib/format";
import type { MyAccessRequest } from "@/lib/types";
import { ClassificationChip, Empty, Loading, Notice, PageHeader, StatusChip } from "@/components/ui";
import { IconChevronDown } from "@/components/Icons";
import { useChat } from "@/components/ChatDock";

function approverLine(request: MyAccessRequest) {
  if (request.status === "pending") {
    return request.approvers.length > 0 ? `Waiting on ${request.approvers.join(", ")}` : "Waiting for an administrator";
  }
  const verb = request.status === "approved" ? "Approved" : "Rejected";
  return `${verb}${request.decided_by ? ` by ${request.decided_by}` : ""}${request.decided_at ? ` · ${formatDateTime(request.decided_at)}` : ""}`;
}

/** Short label for the access window of an approved request. */
function windowOf(request: MyAccessRequest): { label: string; expired: boolean } | null {
  if (request.status !== "approved") return null;
  if (!request.access_expires_at) return { label: "Permanent access", expired: false };
  const expired = parseDate(request.access_expires_at).getTime() <= Date.now();
  return { label: `${expired ? "Expired" : "Until"} ${formatDateTime(request.access_expires_at)}`, expired };
}

export default function WorkspaceRequests() {
  const { openChat } = useChat();
  const { data, error, loading } = useLoad(() => apiRequest<MyAccessRequest[]>("/me/access-requests"));
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <>
      <PageHeader title="Request status" subtitle="Documents you've asked to open. Select a request to see the details." />
      {error && <Notice kind="error">{error}</Notice>}

      {loading ? (
        <div className="panel"><Loading /></div>
      ) : (data?.length ?? 0) === 0 ? (
        <div className="panel">
          <Empty title="You haven't requested access to anything" action={<button className="btn-line" onClick={() => openChat()}>Open the assistant</button>}>
            When the assistant says a document is restricted, use “Request access” in the chat and it will be tracked here.
          </Empty>
        </div>
      ) : (
        <ul className="space-y-2.5">
          {data!.map((request) => {
            const open = openId === request.id;
            const access = windowOf(request);
            return (
              <li key={request.id} className="card overflow-hidden">
                <h2>
                  <button
                    onClick={() => setOpenId(open ? null : request.id)}
                    aria-expanded={open}
                    aria-controls={`req-${request.id}`}
                    className="flex w-full items-center gap-4 px-4 py-3.5 text-left transition-colors hover:bg-white/60 sm:px-5"
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[15px] font-semibold">{request.document_title}</span>
                      <span className="block truncate text-[13px] text-ash">Requested {formatDateTime(request.requested_at)}</span>
                    </span>
                    <span className="flex shrink-0 flex-wrap items-center justify-end gap-2">
                      <span className="hidden sm:inline-flex"><ClassificationChip value={request.classification} /></span>
                      {access && request.access_expires_at && <span className={access.expired ? "chip-soft" : "chip-sky"}>{access.expired ? "Expired" : "Temporary"}</span>}
                      <StatusChip status={request.status} />
                    </span>
                    <IconChevronDown size={18} className={`shrink-0 text-ash transition-transform duration-300 ${open ? "rotate-180" : ""}`} />
                  </button>
                </h2>

                <div id={`req-${request.id}`} aria-hidden={!open} className={`grid transition-all duration-300 ease-out ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}>
                  <div className="overflow-hidden">
                    <dl className="mx-4 mb-4 grid gap-x-8 gap-y-2 border-t border-fog pt-3 text-[13px] sm:mx-5 sm:grid-cols-2">
                      <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">File</dt><dd className="min-w-0 break-words">{request.file_name}</dd></div>
                      <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Classification</dt><dd><ClassificationChip value={request.classification} /></dd></div>
                      <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Requested</dt><dd>{formatDateTime(request.requested_at)}</dd></div>
                      <div className="flex gap-2"><dt className="w-20 shrink-0 text-ash">Approver</dt><dd className="min-w-0 break-words">{approverLine(request)}</dd></div>
                      {access && (
                        <div className="flex gap-2 sm:col-span-2">
                          <dt className="w-20 shrink-0 text-ash">Access</dt>
                          <dd className={access.expired ? "font-semibold text-[#8a1c2f] dark:text-[#ffb3c1]" : "font-semibold"}>
                            {access.label}
                            {access.expired && " — send a new request if you still need it"}
                          </dd>
                        </div>
                      )}
                      <div className="flex gap-2 sm:col-span-2"><dt className="w-20 shrink-0 text-ash">Your reason</dt><dd className="min-w-0 break-words">{request.reason || <span className="text-ash">No reason given</span>}</dd></div>
                    </dl>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </>
  );
}
