"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useEffect, useRef, useState } from "react";
import { useSession } from "@/lib/session";
import { firstName } from "@/lib/format";
import { useTheme } from "@/lib/theme";
import { ChatBubble, ChatProvider, ChatWindow, useChat } from "./ChatDock";
import { IconBuilding, IconCalendar, IconChevronLeft, IconGear, IconLogout, IconMenu, IconMoon, IconSun, IconX } from "./Icons";
import { Avatar } from "./ui";

export type NavItem = { href: string; label: string; icon: ReactNode; badge?: number };

const COLLAPSE_KEY = "ragvault.sidebar";

function LogoMark({ size = 34 }: { size?: number }) {
  return (
    <span
      aria-hidden="true"
      className="inline-flex shrink-0 items-center justify-center rounded-[11px] bg-gradient-to-br from-[#5468d8] to-[#7660d4] shadow-lift"
      style={{ width: size, height: size }}
    >
      <svg width={size * 0.58} height={size * 0.58} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3l8 3v6c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V6z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    </span>
  );
}

export function Shell({ nav, children }: { nav: NavItem[]; children: ReactNode }) {
  return (
    <ChatProvider>
      <ShellBody nav={nav}>{children}</ShellBody>
    </ChatProvider>
  );
}

function ShellBody({ nav, children }: { nav: NavItem[]; children: ReactNode }) {
  const { me, logout } = useSession();
  const { minimize } = useChat();
  const { theme, setTheme, toggle } = useTheme();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [menu, setMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Dashboard-style pages end exactly where the sidebar ends; list pages keep room for the chat bubble.
  const flush = pathname === "/admin" || pathname === "/workspace";
  const main = nav.slice(0, -1);
  const settings = nav[nav.length - 1];
  const home = nav[0].href;

  useEffect(() => {
    try {
      if (localStorage.getItem(COLLAPSE_KEY) === "1") setCollapsed(true);
    } catch {
      /* storage unavailable: stay expanded */
    }
  }, []);

  function toggleCollapsed() {
    setCollapsed((current) => {
      try {
        localStorage.setItem(COLLAPSE_KEY, current ? "0" : "1");
      } catch {
        /* ignore */
      }
      return !current;
    });
  }

  useEffect(() => setDrawer(false), [pathname]);

  useEffect(() => {
    if (!menu) return;
    function onDown(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenu(false);
    }
    function onKey(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setMenu(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [menu]);

  function isActive(href: string) {
    return pathname === href || (href !== "/admin" && href !== "/workspace" && pathname.startsWith(`${href}/`));
  }

  function renderLink(item: NavItem, compact: boolean) {
    const active = isActive(item.href);
    return (
      <Link
        href={item.href}
        title={compact ? item.label : undefined}
        onClick={minimize}
        aria-current={active ? "page" : undefined}
        className={`relative flex items-center gap-3 rounded-xl border py-2.5 text-sm font-semibold transition-colors ${
          compact ? "justify-center px-0" : "px-3.5"
        } ${active ? "border-periwinkle bg-white text-ink shadow-lift" : "border-transparent text-graphite hover:bg-white/70 hover:text-ink"}`}
      >
        <span className={active ? "text-accent" : ""}>{item.icon}</span>
        <span className={compact ? "sr-only" : "flex-1 whitespace-nowrap"}>{item.label}</span>
        {!!item.badge && (
          <span
            className={
              compact
                ? "absolute -right-0.5 -top-1 min-w-[18px] rounded-full bg-periwinkle-deep px-1 text-center text-[11px] font-bold leading-[18px] text-onaccent"
                : "min-w-[24px] rounded-full bg-periwinkle/25 px-1.5 text-center text-xs font-bold leading-5 text-accent"
            }
          >
            {item.badge}
          </span>
        )}
      </Link>
    );
  }

  function renderSidebar(compact: boolean, allowCollapse: boolean) {
    const collapseButton = allowCollapse && (
      <button
        onClick={toggleCollapsed}
        aria-label={compact ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!compact}
        title={compact ? "Expand sidebar" : "Collapse sidebar"}
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-line bg-white text-graphite shadow-lift hover:border-periwinkle hover:text-ink"
      >
        <IconChevronLeft size={16} className={`transition-transform ${compact ? "rotate-180" : ""}`} />
      </button>
    );
    return (
      <nav aria-label="Main" className="flex h-full flex-col p-3">
        <div className={`flex items-center px-1 py-2 ${compact ? "flex-col gap-3" : "justify-between"}`}>
          <Link href={home} onClick={minimize} className="flex items-center gap-2.5" aria-label="RAGVault home">
            <LogoMark />
            {!compact && <span className="text-[19px] font-bold tracking-tight">RAGVault</span>}
          </Link>
          {collapseButton}
        </div>
        <ul className="mt-5 flex-1 space-y-1.5 overflow-y-auto overflow-x-hidden px-1 py-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
          {main.map((item) => (
            <li key={item.href}>{renderLink(item, compact)}</li>
          ))}
        </ul>
        <div className="space-y-1.5 border-t border-fog/80 pt-3">
          {renderLink(settings, compact)}
          <button
            onClick={() => {
              minimize();
              logout();
            }}
            title={compact ? "Log out" : undefined}
            className={`flex w-full items-center gap-3 rounded-xl border border-transparent py-2.5 text-sm font-semibold text-graphite transition-colors hover:bg-white/70 hover:text-ink ${compact ? "justify-center px-0" : "px-3.5"}`}
          >
            <IconLogout />
            <span className={compact ? "sr-only" : ""}>Log out</span>
          </button>
        </div>
      </nav>
    );
  }

  return (
    <div className="h-screen md:p-5">
      <div className="flex h-full gap-4 md:rounded-[36px] md:border md:border-white/70 md:bg-white/30 md:p-4 md:shadow-soft md:backdrop-blur-sm">
        <aside className={`glass hidden shrink-0 rounded-[28px] transition-[width] duration-200 md:block ${collapsed ? "w-[84px]" : "w-[256px]"}`}>
          {renderSidebar(collapsed, true)}
        </aside>

        {drawer && (
          <div className="fixed inset-0 z-40 md:hidden">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setDrawer(false)} />
            <aside className="absolute inset-y-3 left-3 w-[264px] rounded-[28px] border border-line bg-white shadow-soft">
              <button onClick={() => setDrawer(false)} className="absolute right-3 top-4 rounded-xl p-1.5 hover:bg-mist" aria-label="Close menu">
                <IconX size={18} />
              </button>
              {renderSidebar(false, false)}
            </aside>
          </div>
        )}

        <div className="flex min-w-0 flex-1 flex-col px-3 pt-3 md:px-0 md:pt-0">
          <header className="flex h-[60px] shrink-0 items-center gap-3">
            <button onClick={() => setDrawer(true)} className="rounded-xl p-2 hover:bg-white/70 md:hidden" aria-label="Open menu">
              <IconMenu size={20} />
            </button>
            <p className="min-w-0 flex-1 truncate text-[17px] text-graphite sm:text-[19px]">
              Welcome back, <span className="font-bold text-ink">{firstName(me.full_name)}</span>!
            </p>

            <div
              className="hidden items-center gap-2 rounded-full border border-white/80 bg-white/60 px-4 py-2 text-[13px] font-semibold shadow-lift md:flex dark:border-[rgb(255_255_255/0.08)]"
              title="Today"
            >
              <IconCalendar size={16} className="text-accent" />
              <time dateTime={new Date().toISOString().slice(0, 10)}>
                {new Date().toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" })}
              </time>
            </div>

            <button
              onClick={toggle}
              role="switch"
              aria-checked={theme === "dark"}
              aria-label="Dark mode"
              title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              className="relative flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-white/80 bg-white/60 shadow-lift transition hover:bg-white dark:border-[rgb(255_255_255/0.08)]"
            >
              <IconSun size={18} className={`absolute transition-all duration-300 ${theme === "dark" ? "rotate-0 scale-100 opacity-100" : "-rotate-90 scale-50 opacity-0"}`} />
              <IconMoon size={18} className={`absolute transition-all duration-300 ${theme === "dark" ? "rotate-90 scale-50 opacity-0" : "rotate-0 scale-100 opacity-100"}`} />
            </button>

            <div ref={menuRef} className="relative">
              <button
                onClick={() => setMenu((v) => !v)}
                aria-haspopup="dialog"
                aria-expanded={menu}
                aria-label={`Profile: ${me.full_name}`}
                className="flex items-center gap-3 rounded-full py-0.5 pl-0.5 pr-0.5 transition hover:bg-white/50 md:pl-3"
              >
                <span className="hidden text-right md:block">
                  <span className="block max-w-[160px] truncate text-sm font-semibold leading-tight">{me.full_name}</span>
                  <span className="block text-xs leading-tight text-ash">{me.role}</span>
                </span>
                <Avatar name={me.full_name} size={40} />
              </button>

              {menu && (
                <div role="dialog" aria-label="Profile" className="absolute right-0 top-full z-40 mt-3 w-[min(320px,calc(100vw-2rem))] origin-top-right animate-pop rounded-[22px] border border-line bg-white p-5 shadow-soft">
                  <div className="flex items-center gap-3.5">
                    <Avatar name={me.full_name} size={54} />
                    <div className="min-w-0">
                      <p className="truncate text-[16px] font-bold leading-tight">{me.full_name}</p>
                      <p className="truncate text-[13px] text-ash">{me.email}</p>
                      <span className="chip-lav mt-1.5">{me.role}</span>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-2.5 rounded-xl bg-mist px-3.5 py-2.5 text-[13px]">
                    <IconBuilding size={16} className="shrink-0 text-accent" />
                    <span className="text-ash">Company</span>
                    <span className="min-w-0 flex-1 truncate text-right font-semibold">{me.tenant_name}</span>
                  </div>

                  <div className="mt-4">
                    <p className="mb-1.5 text-[12px] font-semibold uppercase tracking-wider text-ash">Appearance</p>
                    <div role="radiogroup" aria-label="Theme" className="grid grid-cols-2 gap-1.5 rounded-xl bg-mist p-1">
                      {([["light", "Light", <IconSun key="s" size={15} />], ["dark", "Dark", <IconMoon key="m" size={15} />]] as const).map(([value, label, icon]) => (
                        <button
                          key={value}
                          role="radio"
                          aria-checked={theme === value}
                          onClick={() => setTheme(value)}
                          className={`flex items-center justify-center gap-2 rounded-lg py-2 text-[13px] font-semibold transition ${theme === value ? "bg-white text-ink shadow-lift" : "text-ash hover:text-ink"}`}
                        >
                          {icon} {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <Link href={settings.href} onClick={() => setMenu(false)} className="btn-line btn-sm justify-center">
                      <IconGear size={15} /> Settings
                    </Link>
                    <button onClick={logout} className="btn-solid btn-sm justify-center">
                      <IconLogout size={15} /> Log out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </header>

          {/* The chat window lives in this region so it opens over the page content, like the wireframe. */}
          <div className="relative min-h-0 flex-1">
            <main className={`h-full overflow-y-auto px-0.5 pt-3 md:pr-1 ${flush ? "pb-0" : "pb-24"}`}>{children}</main>
            <ChatWindow />
            <ChatBubble />
          </div>
        </div>
      </div>
    </div>
  );
}
