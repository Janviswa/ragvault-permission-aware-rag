import Link from "next/link";
import { ReactNode } from "react";

export function Stat({ label, value, note, href, icon, tint }: { label: string; value: number | string; note?: string; href?: string; icon: ReactNode; tint: string }) {
  const body = (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-medium text-ash">{label}</p>
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[#1b2140]" style={{ background: tint }}>{icon}</span>
      </div>
      <p className="mt-2 text-[30px] font-bold leading-none tracking-tight">{value}</p>
      <p className="mt-2 min-h-[20px] text-[13px] text-graphite">{note}</p>
    </>
  );
  const cls = "card block px-5 py-4 transition";
  return href ? <Link href={href} className={`${cls} hover:bg-white/80`}>{body}</Link> : <div className={cls}>{body}</div>;
}
