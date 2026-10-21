"use client";

import { FormEvent, useState } from "react";
import { apiRequest } from "@/lib/api";
import { useSession } from "@/lib/session";
import { useAction, useLoad } from "@/lib/hooks";
import { formatDate } from "@/lib/format";
import type { AdminUser, Role } from "@/lib/types";
import { Avatar, Loading, Modal, Notice, PageHeader } from "@/components/ui";
import { IconPlus } from "@/components/Icons";

const ROLES: Role[] = ["Admin", "Manager", "Employee"];
const ROLE_NOTES: Record<Role, string> = {
  Admin: "Manages people, documents and access. Can read every document in the company.",
  Manager: "Reads documents granted to the Manager role or to them personally.",
  Employee: "Reads documents granted to the Employee role or to them personally.",
};

function generatePassword() {
  const alphabet = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const bytes = crypto.getRandomValues(new Uint32Array(16));
  return Array.from(bytes, (n) => alphabet[n % alphabet.length]).join("");
}

export default function AdminUsers() {
  const { me } = useSession();
  const { data, error, loading, reload } = useLoad(() => apiRequest<AdminUser[]>("/admin/users"));
  const action = useAction();
  const [busyId, setBusyId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);

  async function patch(user: AdminUser, body: Partial<Pick<AdminUser, "role" | "is_active">>, message: string) {
    setBusyId(user.id);
    const ok = await action.run(async () => {
      await apiRequest(`/admin/users/${user.id}`, { method: "PATCH", body: JSON.stringify(body) });
      return message;
    });
    setBusyId(null);
    if (ok) await reload();
  }

  const counts = (role: Role) => (data ?? []).filter((u) => u.role === role).length;

  return (
    <>
      <PageHeader
        title="Users & Roles"
        subtitle="Manage who has an account and what role they hold."
        actions={<button className="btn-solid" onClick={() => setAdding(true)}><IconPlus size={16} /> Add user</button>}
      />
      {error && <Notice kind="error">{error}</Notice>}
      {action.error && <Notice kind="error" onDismiss={action.clear}>{action.error}</Notice>}
      {action.notice && <Notice kind="success" onDismiss={action.clear}>{action.notice}</Notice>}

      <section className="panel mb-8 overflow-hidden" aria-label="People">
        {loading ? <Loading /> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px]">
              <thead className="border-b border-fog"><tr><th className="th">Person</th><th className="th">Role</th><th className="th">Status</th><th className="th">Added</th><th className="th"><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {(data ?? []).map((user) => {
                  const self = user.id === me.id;
                  return (
                    <tr key={user.id} className="row">
                      <td className="td">
                        <div className="flex items-center gap-3">
                          <Avatar name={user.full_name} size={34} />
                          <div className="min-w-0"><p className="truncate font-medium">{user.full_name}{self && <span className="chip-soft ml-2">You</span>}</p><p className="truncate text-[13px] text-ash">{user.email}</p></div>
                        </div>
                      </td>
                      <td className="td">
                        <label className="sr-only" htmlFor={`role-${user.id}`}>Role for {user.full_name}</label>
                        <select id={`role-${user.id}`} className="field w-auto py-1.5" value={user.role} disabled={self || busyId === user.id}
                          title={self ? "You can't change your own role" : undefined}
                          onChange={(e) => patch(user, { role: e.target.value as Role }, `${user.full_name} is now ${e.target.value}.`)}>
                          {ROLES.map((r) => <option key={r}>{r}</option>)}
                        </select>
                      </td>
                      <td className="td">{user.is_active ? <span className="chip-good">Active</span> : <span className="chip-strike">Deactivated</span>}</td>
                      <td className="td text-ash">{formatDate(user.created_at)}</td>
                      <td className="td text-right">
                        {!self && (
                          <button className="btn-line btn-sm" disabled={busyId === user.id}
                            onClick={() => patch(user, { is_active: !user.is_active }, `${user.full_name} was ${user.is_active ? "deactivated" : "reactivated"}.`)}>
                            {user.is_active ? "Deactivate" : "Reactivate"}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <h2 className="mb-3 text-[15px] font-semibold">Roles</h2>
      <div className="grid gap-4 md:grid-cols-3">
        {ROLES.map((role) => (
          <section key={role} className="card p-5">
            <div className="flex items-baseline justify-between"><h3 className="text-base font-semibold">{role}</h3><span className="text-sm text-ash">{counts(role)} {counts(role) === 1 ? "person" : "people"}</span></div>
            <p className="mt-2 text-sm leading-relaxed text-graphite">{ROLE_NOTES[role]}</p>
          </section>
        ))}
      </div>
      <p className="hint mt-3">Deactivated people can't sign in. Their past activity stays in the timeline. Grant document access to a role or a person under Documents.</p>

      {adding && <AddUser onClose={() => setAdding(false)} onCreated={async (name) => { setAdding(false); action.clear(); await reload(); }} />}
    </>
  );
}

function AddUser({ onClose, onCreated }: { onClose: () => void; onCreated: (name: string) => Promise<void> }) {
  const action = useAction();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "Employee" as Role });
  const [created, setCreated] = useState<{ email: string; password: string } | null>(null);
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  async function submit(event: FormEvent) {
    event.preventDefault();
    const ok = await action.run(async () => {
      await apiRequest("/admin/users", { method: "POST", body: JSON.stringify({ ...form, email: form.email.trim(), full_name: form.full_name.trim() }) });
    });
    if (ok) setCreated({ email: form.email.trim(), password: form.password });
  }

  if (created) {
    return (
      <Modal title="Account created" onClose={() => onCreated(created.email)} footer={<button className="btn-solid" onClick={() => onCreated(created.email)}>Done</button>}>
        <p className="text-sm">Share these sign-in details securely. They can change the password under Settings.</p>
        <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-5 gap-y-2 rounded-lg border border-fog bg-mist p-4 text-sm">
          <dt className="text-ash">Email</dt><dd className="break-all font-medium">{created.email}</dd>
          <dt className="text-ash">Password</dt><dd className="break-all font-medium">{created.password}</dd>
        </dl>
        <p className="hint mt-3">This password won't be shown again.</p>
      </Modal>
    );
  }

  return (
    <Modal title="Add user" onClose={onClose}>
      <form onSubmit={submit} className="space-y-4">
        {action.error && <Notice kind="error">{action.error}</Notice>}
        <div><label className="label" htmlFor="nu-name">Full name</label><input id="nu-name" className="field" required maxLength={255} value={form.full_name} onChange={set("full_name")} autoFocus /></div>
        <div><label className="label" htmlFor="nu-email">Work email</label><input id="nu-email" type="email" className="field" required maxLength={255} value={form.email} onChange={set("email")} /></div>
        <div>
          <label className="label" htmlFor="nu-pw">Initial password</label>
          <div className="flex gap-2">
            <input id="nu-pw" className="field" required minLength={12} maxLength={1024} value={form.password} onChange={set("password")} aria-describedby="nu-pw-hint" autoComplete="off" />
            <button type="button" className="btn-line shrink-0" onClick={() => setForm({ ...form, password: generatePassword() })}>Generate</button>
          </div>
          <p id="nu-pw-hint" className="hint mt-1">At least 12 characters.</p>
        </div>
        <div><label className="label" htmlFor="nu-role">Role</label><select id="nu-role" className="field" value={form.role} onChange={set("role")}>{ROLES.map((r) => <option key={r}>{r}</option>)}</select></div>
        <div className="flex justify-end gap-2 pt-2"><button type="button" className="btn-line" onClick={onClose}>Cancel</button><button className="btn-solid" disabled={action.busy}>{action.busy ? "Creating…" : "Create account"}</button></div>
      </form>
    </Modal>
  );
}
