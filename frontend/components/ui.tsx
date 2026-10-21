"use client";

import { ReactNode, useEffect, useRef } from "react";
import { IconAlert, IconCheck, IconX } from "./Icons";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-[26px] font-bold leading-tight tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 max-w-prose text-sm text-graphite">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Notice({ kind, children, onDismiss }: { kind: "error" | "success" | "info"; children: ReactNode; onDismiss?: () => void }) {
  if (!children) return null;
  const Lead = kind === "error" ? IconAlert : IconCheck;
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={`note ${kind === "error" ? "note-error" : kind === "success" ? "note-success" : "note-info"}`}
    >
      {kind !== "info" && <Lead size={16} className="mt-0.5 shrink-0" />}
      <div className="min-w-0 flex-1 break-words">{children}</div>
      {onDismiss && (
        <button onClick={onDismiss} className="-m-1 rounded p-1 opacity-80 hover:opacity-100" aria-label="Dismiss message">
          <IconX size={14} />
        </button>
      )}
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="px-6 py-12 text-center">
      <p className="text-[15px] font-semibold">{title}</p>
      {children && <p className="mx-auto mt-1 max-w-sm text-sm text-graphite">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="px-6 py-12 text-center text-sm text-ash" role="status" aria-live="polite">
      {label}
    </div>
  );
}

export function ClassificationChip({ value }: { value: string }) {
  const cls =
    value === "Restricted" ? "chip-dark"
    : value === "Confidential" ? "chip-lav"
    : value === "Internal" ? "chip-sky"
    : "chip-soft";
  return <span className={cls}>{value}</span>;
}

export function StatusChip({ status }: { status: string }) {
  if (status === "approved") return <span className="chip-good"><IconCheck size={12} /> Approved</span>;
  if (status === "rejected") return <span className="chip-strike"><IconX size={12} /> Rejected</span>;
  return <span className="chip-wait">Pending</span>;
}

export function SeverityChip({ severity }: { severity: string }) {
  const cls = severity === "critical" ? "chip-alert" : severity === "high" ? "chip-strike" : severity === "medium" ? "chip-wait" : "chip-soft";
  return <span className={cls}>{severity}</span>;
}

export function Modal({
  title,
  onClose,
  children,
  wide,
  footer,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
  footer?: ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      previous?.focus?.();
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 backdrop-blur-sm sm:items-center sm:p-6" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={ref}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={`flex max-h-[92vh] w-full flex-col rounded-t-[24px] border border-white bg-white shadow-soft outline-none sm:rounded-[24px] ${wide ? "sm:max-w-3xl" : "sm:max-w-md"}`}
      >
        <div className="flex items-center justify-between gap-4 border-b border-fog px-5 py-4">
          <h2 className="min-w-0 truncate text-base font-semibold">{title}</h2>
          <button onClick={onClose} className="-m-1.5 rounded-xl p-1.5 hover:bg-mist" aria-label="Close">
            <IconX size={18} />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">{children}</div>
        {footer && <div className="flex flex-wrap justify-end gap-2 border-t border-fog px-5 py-4">{footer}</div>}
      </div>
    </div>
  );
}

export function Avatar({ name, size = 36 }: { name: string; size?: number }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex shrink-0 items-center justify-center rounded-full border border-white bg-gradient-to-br from-sky to-lavender font-bold text-[#1b2140] shadow-lift"
      style={{ width: size, height: size, fontSize: size * 0.4 }}
    >
      {(name.trim()[0] ?? "?").toUpperCase()}
    </span>
  );
}

export function downloadText(filename: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
