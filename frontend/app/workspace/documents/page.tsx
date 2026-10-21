"use client";

import { useMemo, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { formatDate, plural } from "@/lib/format";
import type { DocumentDetails, DocumentItem } from "@/lib/types";
import { ClassificationChip, downloadText, Empty, Loading, Modal, Notice, PageHeader } from "@/components/ui";
import { IconChevronDown, IconDownload, IconEye, IconSearch } from "@/components/Icons";
import { useChat } from "@/components/ChatDock";

export default function WorkspaceDocuments() {
  const { openChat } = useChat();
  const { data, error, loading } = useLoad(() => apiRequest<DocumentItem[]>("/documents"));
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const [preview, setPreview] = useState<DocumentDetails | null>(null);
  const action = useAction();

  const documents = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const all = data ?? [];
    return needle ? all.filter((d) => `${d.title} ${d.file_name}`.toLowerCase().includes(needle)) : all;
  }, [data, query]);

  async function fetchDetails(id: number) {
    return apiRequest<DocumentDetails>(`/documents/${id}`);
  }

  function onPreview(doc: DocumentItem) {
    action.run(async () => {
      setPreview(await fetchDetails(doc.id));
    });
  }

  function onDownload(doc: DocumentItem) {
    action.run(async () => {
      const details = await fetchDetails(doc.id);
      downloadText(`${doc.file_name.replace(/\.[^.]+$/, "")}.txt`, details.content ?? "");
      return `Downloaded ${doc.title}.`;
    });
  }

  return (
    <>
      <PageHeader title="Documents" subtitle="Documents you can open, based on your role and any access you've been granted." />

      {error && <Notice kind="error">{error}</Notice>}
      {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
      {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}

      <div className="panel">
        <div className="panel-head">
          <h2 className="text-[15px] font-semibold">Available documents{data ? ` (${data.length})` : ""}</h2>
          {(data?.length ?? 0) > 0 && (
            <div className="relative w-full sm:w-64">
              <IconSearch size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ash" />
              <label htmlFor="doc-search" className="sr-only">Search documents</label>
              <input id="doc-search" className="field pl-9" placeholder="Search documents" value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>
          )}
        </div>

        {loading ? (
          <Loading />
        ) : (data?.length ?? 0) === 0 ? (
          <Empty
            title="No documents are shared with you yet"
            action={<button className="btn-line" onClick={() => openChat()}>Ask the assistant</button>}
          >
            Ask the assistant about a topic. If the answer is in a document you can't open, you can request access right from the chat.
          </Empty>
        ) : documents.length === 0 ? (
          <Empty title="No matches">Nothing matches “{query}”.</Empty>
        ) : (
          <ul>
            {documents.map((doc) => {
              const open = openId === doc.id;
              return (
                <li key={doc.id} className="row">
                  <h3>
                    <button
                      onClick={() => setOpenId(open ? null : doc.id)}
                      aria-expanded={open}
                      aria-controls={`doc-${doc.id}`}
                      className="flex w-full items-center gap-4 px-5 py-4 text-left hover:bg-mist"
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[15px] font-medium">{doc.title}</span>
                        <span className="mt-0.5 block truncate text-[13px] text-ash">{doc.file_name}</span>
                      </span>
                      <span className="hidden sm:block"><ClassificationChip value={doc.classification} /></span>
                      <IconChevronDown size={18} className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
                    </button>
                  </h3>
                  {open && (
                    <div id={`doc-${doc.id}`} className="border-t border-fog bg-mist px-5 py-4">
                      {doc.summary ? (
                        <p className="max-w-prose text-sm leading-relaxed text-graphite">{doc.summary}{doc.summary.length >= 240 ? "…" : ""}</p>
                      ) : (
                        <p className="text-sm text-ash">No text preview available.</p>
                      )}
                      <p className="mt-3 text-[13px] text-ash">
                        <span className="sm:hidden">{doc.classification} · </span>
                        {plural(doc.word_count, "word")} · Added {formatDate(doc.created_at)}
                      </p>
                      <div className="mt-4 flex flex-wrap items-center gap-2">
                        <button className="btn-solid btn-sm" disabled={action.busy} onClick={() => onPreview(doc)}>
                          <IconEye size={15} /> Preview
                        </button>
                        <button className="btn-line btn-sm" disabled={action.busy} onClick={() => onDownload(doc)}>
                          <IconDownload size={15} /> Download
                        </button>
                        <span className="text-xs text-ash">Downloads the indexed text version (.txt).</span>
                      </div>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {preview && (
        <Modal
          wide
          title={preview.title}
          onClose={() => setPreview(null)}
          footer={
            <>
              <button className="btn-line" onClick={() => downloadText(`${preview.file_name.replace(/\.[^.]+$/, "")}.txt`, preview.content ?? "")}>
                <IconDownload size={15} /> Download
              </button>
              <button className="btn-solid" onClick={() => setPreview(null)}>Close</button>
            </>
          }
        >
          <p className="mb-3 text-[13px] text-ash">{preview.file_name} · {preview.classification}</p>
          <pre className="max-h-[55vh] overflow-auto whitespace-pre-wrap break-words rounded-lg border border-fog bg-mist p-4 font-sans text-sm leading-relaxed">
            {preview.content || "This document has no text content."}
          </pre>
        </Modal>
      )}
    </>
  );
}
