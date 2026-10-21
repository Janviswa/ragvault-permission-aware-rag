import { ReactNode } from "react";

/** Small hover/focus label for icon-only buttons. The button should still carry its own aria-label. */
export function Tip({ label, children, align = "center", side = "bottom" }: { label: string; children: ReactNode; align?: "center" | "end"; side?: "top" | "bottom" }) {
  return (
    <span className="group/tip relative inline-flex">
      {children}
      <span
        role="tooltip"
        className={`pointer-events-none absolute z-50 whitespace-nowrap rounded-lg bg-[#1b2140] px-2.5 py-1 text-[12px] font-semibold text-white opacity-0 shadow-soft transition-opacity duration-150 group-hover/tip:opacity-100 group-hover/tip:delay-200 group-focus-within/tip:opacity-100 dark:bg-[#e9ecff] dark:text-[#1b2140] ${
          side === "bottom" ? "top-full mt-2" : "bottom-full mb-2"
        } ${align === "end" ? "right-0" : "left-1/2 -translate-x-1/2"}`}
      >
        {label}
      </span>
    </span>
  );
}
