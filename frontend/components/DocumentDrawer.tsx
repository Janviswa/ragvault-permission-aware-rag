"use client";

import { FormEvent, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useAction, useLoad } from "@/lib/hooks";
import { formatDateTime } from "@/lib/format";
import type { AdminUser, DocumentDetails, DocumentItem, Permission, TemporaryAccess } from "@/lib/types";
import { Loading, Modal, Notice } from "./ui";
import { IconEye, IconTrash, IconX } from "./Icons";

const CLASSIFICATIONS = ["Public", "Internal", "Confidential", "Restricted"];
const GRANTABLE_ROLES = ["Employee", "Manager"];

function localInput(date: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function DocumentDrawer({ doc, users, onClose, onChanged }: { doc: DocumentItem; users: AdminUser[]; onClose: () => void; onChanged: () => Promise<void> }) {
  const action = useAction();
  const perms = useLoad(() => apiRequest<Permission[]>(`/documents/${doc.id}/permissions`), [doc.id]);
  const temps = useLoad(async () => (await apiRequest<TemporaryAccess[]>("/admin/security/temporary-access")).filter((t) => t.document_id === doc.id), [doc.id]);
  const [title, setTitle] = useState(doc.title);
  const [classification, setClassification] = useState(doc.classification);
  const [target, setTarget] = useState<"role" | "user">("role");
  const [role, setRole] = useState(GRANTABLE_ROLES[0]);
  const [userId, setUserId] = useState("");
  const [tempUser, setTempUser] = useState("");
  const [expires, setExpires] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [text, setText] = useState<DocumentDetails | null>(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && !text && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose, text]);

  const userName = (id: number | null) => users.find((u) => u.id === id)?.full_name ?? `User #${id}`;
  const nonAdmins = users.filter((u) => u.is_active && u.role !== "Admin");

  const save = (e: FormEvent) => { e.preventDefault(); return action.run(async () => {
    await apiRequest(`/documents/${doc.id}`, { method: "PATCH", body: JSON.stringify({ title: title.trim(), classification }) });
    await onChanged();
    return "Details saved. The document was re-indexed.";
  }); };

  const grant = (e: FormEvent) => { e.preventDefault(); return action.run(async () => {
    await apiRequest(`/documents/${doc.id}/permissions`, { method: "POST", body: JSON.stringify(target === "role" ? { role, permission: "read" } : { user_id: Number(userId), permission: "read" }) });
    setUserId("");
    await perms.reload();
    return "Read access granted.";
  }); };

  const revoke = (p: Permission) => action.run(async () => {
    await apiRequest(`/documents/${doc.id}/permissions/${p.id}`, { method: "DELETE" });
    await perms.reload();
    return "Read access removed.";
  });

  const grantTemp = (e: FormEvent) => { e.preventDefault(); return action.run(async () => {
    await apiRequest(`/documents/${doc.id}/temporary-access`, { method: "POST", body: JSON.stringify({ user_id: Number(tempUser), expires_at: new Date(expires).toISOString() }) });
    setTempUser(""); setExpires("");
    await temps.reload();
    return "Temporary access granted.";
  }); };

  const revokeTemp = (t: TemporaryAccess) => action.run(async () => {
    await apiRequest(`/documents/${doc.id}/temporary-access/${t.id}`, { method: "DELETE" });
    await temps.reload();
    return "Temporary access ended.";
  });

  const remove = () => action.run(async () => {
    await apiRequest(`/documents/${doc.id}`, { method: "DELETE" });
    await onChanged();
    onClose();
  });

  const preset = (hours: number) => setExpires(localInput(new Date(Date.now() + hours * 3_600_000)));

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <aside role="dialog" aria-modal="true" aria-label={`Manage ${doc.title}`} className="absolute inset-y-0 right-0 flex w-full max-w-xl flex-col border-l border-white bg-white/95 shadow-soft sm:inset-y-3 sm:right-3 sm:rounded-[24px] sm:border">
        <div className="flex items-start justify-between gap-4 border-b border-fog px-5 py-4">
          <div className="min-w-0"><h2 className="truncate text-lg font-semibold">{doc.title}</h2><p className="text-[13px] text-ash">{doc.file_name} · #{doc.id}</p></div>
          <button onClick={onClose} className="-m-1.5 rounded-lg p-1.5 hover:bg-mist" aria-label="Close"><IconX size={18} /></button>
        </div>

        <div className="min-h-0 flex-1 space-y-8 overflow-y-auto px-5 py-6">
          {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
          {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}

          <section aria-labelledby="d-details">
            <h3 id="d-details" className="mb-3 text-[15px] font-semibold">Details</h3>
            <form onSubmit={save} className="space-y-3">
              <div><label className="label" htmlFor="d-title">Title</label><input id="d-title" className="field" required maxLength={255} value={title} onChange={(e) => setTitle(e.target.value)} /></div>
              <div><label className="label" htmlFor="d-class">Classification</label><select id="d-class" className="field" value={classification} onChange={(e) => setClassification(e.target.value)}>{CLASSIFICATIONS.map((c) => <option key={c}>{c}</option>)}</select></div>
              <div className="flex gap-2">
                <button className="btn-solid" disabled={action.busy || (title === doc.title && classification === doc.classification)}>Save details</button>
                <button type="button" className="btn-line" onClick={() => action.run(async () => { setText(await apiRequest<DocumentDetails>(`/documents/${doc.id}`)); })}><IconEye size={15} /> View text</button>
              </div>
            </form>
          </section>

          <section aria-labelledby="d-access">
            <h3 id="d-access" className="text-[15px] font-semibold">Who can read this</h3>
            <p className="hint mb-3 mt-0.5">Admins can always read every document.</p>
            {perms.loading ? <Loading /> : (perms.data?.length ?? 0) === 0 ? <p className="rounded-lg border border-dashed border-ash px-4 py-3 text-sm text-graphite">Nobody else yet. Only admins can read this.</p> : (
              <ul className="rounded-xl border border-line bg-white/70">
                {perms.data!.map((p) => (
                  <li key={p.id} className="row flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                    <span>{p.user_id ? userName(p.user_id) : <>Everyone with the <b>{p.role}</b> role</>}</span>
                    <button className="btn-quiet btn-sm" disabled={action.busy} onClick={() => revoke(p)} aria-label={`Remove access for ${p.user_id ? userName(p.user_id) : p.role}`}>Remove</button>
                  </li>
                ))}
              </ul>
            )}
            <form onSubmit={grant} className="mt-3 flex flex-wrap items-end gap-2">
              <div><label className="label" htmlFor="g-target">Grant to</label><select id="g-target" className="field w-auto" value={target} onChange={(e) => setTarget(e.target.value as "role" | "user")}><option value="role">A role</option><option value="user">A person</option></select></div>
              <div className="min-w-[160px] flex-1">
                <label className="label" htmlFor="g-who">{target === "role" ? "Role" : "Person"}</label>
                {target === "role" ? (
                  <select id="g-who" className="field" value={role} onChange={(e) => setRole(e.target.value)}>{GRANTABLE_ROLES.map((r) => <option key={r}>{r}</option>)}</select>
                ) : (
                  <select id="g-who" className="field" required value={userId} onChange={(e) => setUserId(e.target.value)}><option value="">Choose a person</option>{nonAdmins.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select>
                )}
              </div>
              <button className="btn-solid" disabled={action.busy}>Grant read access</button>
            </form>
          </section>

          <section aria-labelledby="d-temp">
            <h3 id="d-temp" className="text-[15px] font-semibold">Temporary access</h3>
            <p className="hint mb-3 mt-0.5">Lets one person read this until a set time, then stops automatically.</p>
            {(temps.data?.length ?? 0) > 0 && (
              <ul className="mb-3 rounded-xl border border-line bg-white/70">
                {temps.data!.map((t) => (
                  <li key={t.id} className="row flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
                    <span>{userName(t.user_id)} <span className="text-ash">until {formatDateTime(t.expires_at)}</span></span>
                    <button className="btn-quiet btn-sm" disabled={action.busy} onClick={() => revokeTemp(t)}>End now</button>
                  </li>
                ))}
              </ul>
            )}
            <form onSubmit={grantTemp} className="space-y-2">
              <div className="flex flex-wrap gap-2">
                <div className="min-w-[160px] flex-1"><label className="label" htmlFor="t-user">Person</label><select id="t-user" className="field" required value={tempUser} onChange={(e) => setTempUser(e.target.value)}><option value="">Choose a person</option>{nonAdmins.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}</select></div>
                <div className="min-w-[200px] flex-1"><label className="label" htmlFor="t-exp">Expires</label><input id="t-exp" type="datetime-local" className="field" required value={expires} onChange={(e) => setExpires(e.target.value)} /></div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button className="btn-solid" disabled={action.busy}>Grant temporary access</button>
                <span className="text-[13px] text-ash">Quick set:</span>
                {[[1, "1 hour"], [24, "1 day"], [168, "1 week"]].map(([h, l]) => <button key={l} type="button" className="btn-quiet btn-sm" onClick={() => preset(h as number)}>{l}</button>)}
              </div>
            </form>
          </section>

          <section aria-labelledby="d-danger" className="border-t border-fog pt-6">
            <h3 id="d-danger" className="mb-2 text-[15px] font-semibold">Delete document</h3>
            <p className="hint mb-3">Removes the document, its index entries, all grants and any access requests. This can't be undone.</p>
            {confirmDelete ? (
              <div className="flex items-center gap-2"><button className="btn-solid" disabled={action.busy} onClick={remove}>Yes, delete it</button><button className="btn-quiet" onClick={() => setConfirmDelete(false)}>Cancel</button></div>
            ) : <button className="btn-line" onClick={() => setConfirmDelete(true)}><IconTrash size={15} /> Delete document</button>}
          </section>
        </div>
      </aside>

      {text && (
        <Modal wide title={text.title} onClose={() => setText(null)} footer={<button className="btn-solid" onClick={() => setText(null)}>Close</button>}>
          <pre className="max-h-[55vh] overflow-auto whitespace-pre-wrap break-words rounded-lg border border-fog bg-mist p-4 font-sans text-sm leading-relaxed">{text.content || "No text content."}</pre>
        </Modal>
      )}
    </div>
  );
}
