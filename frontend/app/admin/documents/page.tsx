"use client";

import { ChangeEvent, useRef, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { formatDate } from "@/lib/format";
import type { AdminUser, DocumentItem } from "@/lib/types";
import { ClassificationChip, Empty, Loading, Notice, PageHeader } from "@/components/ui";
import { DocumentDrawer } from "@/components/DocumentDrawer";
import { IconUpload } from "@/components/Icons";

export default function AdminDocuments() {
  const docs = useLoad(() => apiRequest<DocumentItem[]>("/documents"));
  const users = useLoad(() => apiRequest<AdminUser[]>("/admin/users"));
  const upload = useAction();
  const fileRef = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const current = docs.data?.find((d) => d.id === selected) ?? null;

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const ok = await upload.run(async () => {
      const form = new FormData();
      form.append("file", file);
      const result = await apiRequest<{ message: string; document_id: number; chunks_created: number }>("/documents/upload", { method: "POST", body: form });
      return `${file.name} was added and indexed (${result.chunks_created} passages). Only admins can read it until you grant access.`;
    });
    if (ok) await docs.reload();
  }

  return (
    <>
      <PageHeader
        title="Documents"
        subtitle="Indexed documents and who can read them."
        actions={<>
          <input ref={fileRef} type="file" accept=".txt,.pdf,.docx" className="sr-only" onChange={onFile} aria-label="Choose a TXT, PDF or DOCX file to upload" tabIndex={-1} />
          <button className="btn-solid" disabled={upload.busy} onClick={() => fileRef.current?.click()}><IconUpload size={16} /> {upload.busy ? "Uploading and indexing…" : "Upload document"}</button>
        </>}
      />
      {docs.error && <Notice kind="error">{docs.error}</Notice>}
      {upload.error && <Notice kind="error" onDismiss={upload.clear}>{upload.error}</Notice>}
      {upload.notice && <Notice kind="success" onDismiss={upload.clear}>{upload.notice}</Notice>}
      <p className="hint mb-3">TXT, PDF or DOCX, up to 10 MB.</p>

      <section className="panel overflow-hidden" aria-label="Documents">
        {docs.loading ? <Loading /> : (docs.data?.length ?? 0) === 0 ? (
          <Empty title="No documents yet" action={<button className="btn-solid" onClick={() => fileRef.current?.click()}>Upload the first one</button>}>Uploaded documents are indexed so the assistant can answer from them.</Empty>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[620px]">
              <thead className="border-b border-fog"><tr><th className="th">Document</th><th className="th">Classification</th><th className="th">Added</th><th className="th"><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {docs.data!.map((d) => (
                  <tr key={d.id} className="row">
                    <td className="td"><p className="font-medium">{d.title}</p><p className="text-[13px] text-ash">{d.file_name}</p></td>
                    <td className="td"><ClassificationChip value={d.classification} /></td>
                    <td className="td text-ash">{formatDate(d.created_at)}</td>
                    <td className="td text-right"><button className="btn-line btn-sm" onClick={() => setSelected(d.id)} aria-label={`Manage ${d.title}`}>Manage</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {current && users.data && <DocumentDrawer key={current.id} doc={current} users={users.data} onClose={() => setSelected(null)} onChanged={docs.reload} />}
    </>
  );
}
