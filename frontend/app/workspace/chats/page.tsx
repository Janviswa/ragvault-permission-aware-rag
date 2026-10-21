"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { chatBucket, formatDateTime, plural } from "@/lib/format";
import type { ChatSummary } from "@/lib/types";
import { Empty, Loading, Notice, PageHeader } from "@/components/ui";
import { IconEye, IconNewChat, IconTrash } from "@/components/Icons";
import { useChat } from "@/components/ChatDock";

const ORDER = ["Today", "This week", "Earlier"] as const;

export default function WorkspaceChats() {
  const { openChat, version } = useChat();
  const { data, error, loading, reload } = useLoad(() => apiRequest<ChatSummary[]>("/chats"));
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const action = useAction();

  // Pick up conversations started or continued in the assistant window.
  useEffect(() => {
    if (version > 0) reload();
  }, [version, reload]);

  const groups = useMemo(() => {
    const buckets: Record<string, ChatSummary[]> = { Today: [], "This week": [], Earlier: [] };
    for (const chat of data ?? []) buckets[chatBucket(chat.updated_at)].push(chat);
    return ORDER.map((label) => ({ label, chats: buckets[label] })).filter((g) => g.chats.length > 0);
  }, [data]);

  async function remove(id: number) {
    const ok = await action.run(async () => {
      await apiRequest(`/chats/${id}`, { method: "DELETE" });
      return "Chat deleted.";
    });
    if (ok) {
      setConfirmId(null);
      await reload();
    }
  }

  return (
    <>
      <PageHeader
        title="Chat history"
        subtitle="Your past conversations with the assistant. Only you can see them."
        actions={<button className="btn-solid" onClick={() => openChat()}><IconNewChat size={16} /> New chat</button>}
      />

      {error && <Notice kind="error">{error}</Notice>}
      {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
      {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}

      {loading ? (
        <div className="panel"><Loading /></div>
      ) : groups.length === 0 ? (
        <div className="panel">
          <Empty title="No chats yet" action={<button className="btn-solid" onClick={() => openChat()}>Start a chat</button>}>
            Conversations you have with the assistant will show up here.
          </Empty>
        </div>
      ) : (
        <div className="space-y-8">
          {groups.map((group) => (
            <section key={group.label} aria-labelledby={`g-${group.label}`}>
              <h2 id={`g-${group.label}`} className="mb-2 text-sm font-semibold">{group.label}</h2>
              <ul className="space-y-2">
                {group.chats.map((chat) => (
                  <li key={chat.id} className="card flex flex-wrap items-center gap-3 px-4 py-3">
                    <div className="min-w-0 flex-1 basis-56">
                      <p className="truncate text-[15px] font-medium">{chat.title}</p>
                      <p className="mt-0.5 text-[13px] text-ash">{formatDateTime(chat.updated_at)} · {plural(Math.ceil(chat.message_count / 2), "question")}</p>
                    </div>
                    {confirmId === chat.id ? (
                      <div className="flex items-center gap-2" role="group" aria-label={`Confirm deleting ${chat.title}`}>
                        <span className="text-[13px]">Delete this chat?</span>
                        <button className="btn-solid btn-sm" disabled={action.busy} onClick={() => remove(chat.id)}>Delete</button>
                        <button className="btn-quiet btn-sm" onClick={() => setConfirmId(null)}>Cancel</button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button className="btn-line btn-sm" onClick={() => openChat(chat.id)}><IconEye size={15} /> Preview</button>
                        <button className="btn-quiet btn-sm" onClick={() => setConfirmId(chat.id)} aria-label={`Delete chat ${chat.title}`}>
                          <IconTrash size={15} /> Delete
                        </button>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </>
  );
}
