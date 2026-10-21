"use client";

import { FormEvent, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useAction } from "@/lib/hooks";
import { Avatar, Notice, PageHeader } from "./ui";
import { IconCheck, IconLogout, IconPencil } from "./Icons";
import type { Me } from "@/lib/types";

export function SettingsView() {
  const { me, logout, updateMe } = useSession();
  const action = useAction();
  const profile = useAction();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(me.full_name);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    if (next !== confirm) {
      setMismatch(true);
      return;
    }
    setMismatch(false);
    const ok = await action.run(async () => {
      await apiRequest("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: current, new_password: next }),
      });
      return "Password updated. Use it the next time you sign in.";
    });
    if (ok) {
      setCurrent("");
      setNext("");
      setConfirm("");
    }
  }

  async function saveName(event: FormEvent) {
    event.preventDefault();
    const cleaned = name.trim().replace(/\s+/g, " ");
    if (!cleaned) return;
    if (cleaned === me.full_name) {
      setEditing(false);
      return;
    }
    const ok = await profile.run(async () => {
      const updated = await apiRequest<Me>("/auth/me", { method: "PATCH", body: JSON.stringify({ full_name: cleaned }) });
      updateMe(updated);
      return "Name updated.";
    });
    if (ok) setEditing(false);
  }

  const rows: [string, string][] = [
    ["Email", me.email],
    ["Role", me.role],
    ["Company", me.tenant_name],
  ];

  return (
    <>
      <PageHeader title="Settings" subtitle="Your account and sign-in." />

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel" aria-labelledby="profile-title">
          <div className="panel-head"><h2 id="profile-title" className="text-[15px] font-semibold">Profile</h2></div>
          <div className="flex items-center gap-4 px-5 pt-5">
            <Avatar name={me.full_name} size={52} />
            <div className="min-w-0">
              <p className="truncate text-base font-semibold">{me.full_name}</p>
              <p className="text-sm text-ash">{me.role}</p>
            </div>
          </div>
          <div className="px-5 pt-5">
            {profile.error && <Notice kind="error" onDismiss={profile.clear}>{profile.error}</Notice>}
            {profile.notice && !editing && <Notice kind="success" onDismiss={profile.clear}>{profile.notice}</Notice>}
            {editing ? (
              <form onSubmit={saveName} className="space-y-2">
                <label htmlFor="display-name" className="label">Display name</label>
                <div className="flex flex-wrap gap-2">
                  <input
                    id="display-name"
                    className="field min-w-[200px] flex-1"
                    value={name}
                    maxLength={255}
                    required
                    autoFocus
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Escape") { setEditing(false); setName(me.full_name); profile.clear(); } }}
                  />
                  <button className="btn-solid" disabled={profile.busy || !name.trim()}><IconCheck size={16} /> {profile.busy ? "Saving…" : "Save"}</button>
                  <button type="button" className="btn-line" disabled={profile.busy} onClick={() => { setEditing(false); setName(me.full_name); profile.clear(); }}>Cancel</button>
                </div>
                <p className="hint">This is how your name appears to you and to admins. Your email and role are managed by an admin.</p>
              </form>
            ) : (
              <div className="flex items-center justify-between gap-3 rounded-xl bg-mist px-4 py-3">
                <div className="min-w-0">
                  <p className="text-[12px] font-semibold uppercase tracking-wider text-ash">Display name</p>
                  <p className="truncate text-sm font-semibold">{me.full_name}</p>
                </div>
                <button className="btn-line btn-sm shrink-0" onClick={() => { setName(me.full_name); profile.clear(); setEditing(true); }}>
                  <IconPencil size={14} /> Change name
                </button>
              </div>
            )}
          </div>
          <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2.5 px-5 py-5 text-sm">
            {rows.map(([label, value]) => (
              <div key={label} className="contents">
                <dt className="text-ash">{label}</dt>
                <dd className="min-w-0 break-words">{value}</dd>
              </div>
            ))}
          </dl>
          <div className="border-t border-fog px-5 py-4">
            <button className="btn-line" onClick={logout}><IconLogout size={16} /> Sign out</button>
          </div>
        </section>

        <section className="panel" aria-labelledby="password-title">
          <div className="panel-head"><h2 id="password-title" className="text-[15px] font-semibold">Change password</h2></div>
          <form onSubmit={changePassword} className="space-y-4 px-5 py-5">
            {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
            {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}
            <div>
              <label htmlFor="cur" className="label">Current password</label>
              <input id="cur" type="password" autoComplete="current-password" required className="field" value={current} onChange={(e) => setCurrent(e.target.value)} />
            </div>
            <div>
              <label htmlFor="new" className="label">New password</label>
              <input id="new" type="password" autoComplete="new-password" required minLength={12} className="field" value={next} onChange={(e) => setNext(e.target.value)} aria-describedby="new-hint" />
              <p id="new-hint" className="hint mt-1">At least 12 characters.</p>
            </div>
            <div>
              <label htmlFor="conf" className="label">Confirm new password</label>
              <input id="conf" type="password" autoComplete="new-password" required className="field" value={confirm} onChange={(e) => { setConfirm(e.target.value); setMismatch(false); }} aria-invalid={mismatch} />
              {mismatch && <p role="alert" className="mt-1 text-[13px] font-medium">The two passwords don't match.</p>}
            </div>
            <button className="btn-solid" disabled={action.busy}>{action.busy ? "Saving…" : "Update password"}</button>
          </form>
        </section>
      </div>
    </>
  );
}
