"use client";

import { KeyboardEvent, PointerEvent, useEffect, useRef, useState } from "react";
import type { ActivityPoint, AnalyticsRange } from "@/lib/types";
import { IconBarChart, IconLineChart } from "./Icons";
import { Tip } from "./Tip";

export const RANGES: { key: AnalyticsRange; label: string; long: string }[] = [
  { key: "7d", label: "7 days", long: "last 7 days" },
  { key: "1m", label: "1M", long: "last month" },
  { key: "3m", label: "3M", long: "last 3 months" },
];

type Mode = "bars" | "line";
const MODE_KEY = "ragvault.chartMode";
const HEIGHT = 208;
const COLOR_A = "#8da2f0";
const COLOR_B = "#7fd0e6";

/** Round the top of the y axis to something readable (even for small counts, 1/2/5 steps above 10). */
function axisMax(peak: number): number {
  if (peak <= 10) return Math.max(4, Math.ceil(peak / 2) * 2);
  const pow = 10 ** Math.floor(Math.log10(peak));
  const f = peak / pow;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * pow;
}

/** Smooth curve that never overshoots the data (monotone cubic, same idea as d3's curveMonotoneX). */
function smoothPath(points: [number, number][]): string {
  const n = points.length;
  if (n === 0) return "";
  if (n === 1) return `M${points[0][0]},${points[0][1]}`;
  const sign = (v: number) => (v < 0 ? -1 : 1);
  const dx = (i: number) => points[i + 1][0] - points[i][0];
  const slope = (i: number) => (points[i + 1][1] - points[i][1]) / dx(i);
  const m: number[] = new Array(n);
  if (n === 2) {
    m[0] = m[1] = slope(0);
  } else {
    for (let i = 1; i < n - 1; i++) {
      const s0 = slope(i - 1);
      const s1 = slope(i);
      const p = (s0 * dx(i) + s1 * dx(i - 1)) / (dx(i - 1) + dx(i));
      m[i] = (sign(s0) + sign(s1)) * Math.min(Math.abs(s0), Math.abs(s1), 0.5 * Math.abs(p)) || 0;
    }
    m[0] = (3 * slope(0) - m[1]) / 2;
    m[n - 1] = (3 * slope(n - 2) - m[n - 2]) / 2;
  }
  let d = `M${points[0][0]},${points[0][1]}`;
  for (let i = 0; i < n - 1; i++) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[i + 1];
    const step = (x1 - x0) / 3;
    d += `C${x0 + step},${y0 + step * m[i]},${x1 - step},${y1 - step * m[i + 1]},${x1},${y1}`;
  }
  return d;
}

type Props = {
  title: string;
  labels: { a: string; b: string };
  data: ActivityPoint[];
  range: AnalyticsRange;
  onRange: (range: AnalyticsRange) => void;
  bucketDays: number;
  busy?: boolean;
};

export function ActivityPanel({ title, labels, data, range, onRange, bucketDays, busy = false }: Props) {
  const [mode, setMode] = useState<Mode>("bars");
  const [hover, setHover] = useState<number | null>(null);
  const [width, setWidth] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(MODE_KEY);
      if (saved === "bars" || saved === "line") setMode(saved);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    setWidth(el.clientWidth);
    const observer = new ResizeObserver(() => setWidth(el.clientWidth));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => setHover(null), [range, mode]);

  function chooseMode(next: Mode) {
    setMode(next);
    try {
      localStorage.setItem(MODE_KEY, next);
    } catch {
      /* ignore */
    }
  }

  const n = data.length;
  const peak = Math.max(0, ...data.flatMap((d) => [d.queries, d.document_views]));
  const max = axisMax(peak);
  const ticks = [max, max / 2, 0];
  const slot = n ? width / n : 0;
  const cx = (i: number) => (i + 0.5) * slot;
  const y = (v: number) => HEIGHT - (v / max) * (HEIGHT - 8);
  const last = n - 1;
  const questions = data.reduce((sum, d) => sum + d.queries, 0);
  const opened = data.reduce((sum, d) => sum + d.document_views, 0);
  const day = (iso: string) => new Date(`${iso}T00:00:00`);

  const rangeText = (iso: string) => {
    const start = day(iso);
    if (bucketDays === 1) return start.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" });
    const end = new Date(start);
    end.setDate(end.getDate() + bucketDays - 1);
    const f = (d: Date) => d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
    return `${f(start)} – ${f(end)}`;
  };
  const tickLabel = (iso: string, i: number) => {
    if (range === "7d") return day(iso).toLocaleDateString(undefined, { weekday: "short" });
    const every = range === "1m" ? 5 : 2;
    return i % every === 0 || i === last ? day(iso).toLocaleDateString(undefined, { day: "numeric", month: "short" }) : "";
  };

  function move(event: PointerEvent<HTMLDivElement>) {
    if (!slot) return;
    const rect = event.currentTarget.getBoundingClientRect();
    setHover(Math.min(n - 1, Math.max(0, Math.floor((event.clientX - rect.left) / slot))));
  }
  function key(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "ArrowRight") setHover((h) => Math.min(n - 1, (h ?? -1) + 1));
    else if (event.key === "ArrowLeft") setHover((h) => Math.max(0, (h ?? n) - 1));
    else if (event.key === "Home") setHover(0);
    else if (event.key === "End") setHover(last);
    else if (event.key === "Escape") setHover(null);
    else return;
    event.preventDefault();
  }

  const bw = Math.max(4, Math.min(26, slot * 0.32));
  const active = hover !== null ? data[hover] : null;
  const tipLeft = hover !== null ? Math.min(Math.max(cx(hover), 100), Math.max(100, width - 100)) : 0;
  const tipTop = active ? Math.max(4, y(Math.max(active.queries, active.document_views)) - 92) : 0;

  const pointsA: [number, number][] = data.map((d, i) => [cx(i), y(d.queries)]);
  const pointsB: [number, number][] = data.map((d, i) => [cx(i), y(d.document_views)]);
  const lineA = smoothPath(pointsA);
  const lineB = smoothPath(pointsB);
  const showDots = n <= 13;

  return (
    <section className="panel" aria-labelledby="act-title">
      <div className="panel-head">
        <h2 id="act-title" className="text-[15px] font-bold">{title}</h2>
        <div className="flex flex-wrap items-center gap-2">
          <div role="radiogroup" aria-label="Chart type" className="flex gap-1 rounded-full bg-mist p-1">
            {([["bars", "Bar chart", <IconBarChart key="b" size={15} />], ["line", "Line graph", <IconLineChart key="l" size={15} />]] as const).map(([value, label, icon]) => (
              <Tip key={value} label={label}>
                <button
                  role="radio"
                  aria-checked={mode === value}
                  aria-label={label}
                  onClick={() => chooseMode(value)}
                  className={`flex h-7 w-8 items-center justify-center rounded-full transition ${mode === value ? "bg-periwinkle-deep text-onaccent shadow-lift" : "text-ash hover:text-ink"}`}
                >
                  {icon}
                </button>
              </Tip>
            ))}
          </div>
          <div role="radiogroup" aria-label="Time range" className="flex gap-1 rounded-full bg-mist p-1">
            {RANGES.map((r) => (
              <button
                key={r.key}
                role="radio"
                aria-checked={range === r.key}
                onClick={() => onRange(r.key)}
                className={`rounded-full px-3.5 py-1 text-[13px] font-semibold transition ${range === r.key ? "bg-periwinkle-deep text-onaccent shadow-lift" : "text-ash hover:text-ink"}`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className={`px-5 py-5 transition-opacity ${busy ? "opacity-60" : ""}`}>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2 text-[13px]">
          <div className="flex gap-5">
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR_A }} /> {labels.a}</span>
            <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR_B }} /> {labels.b}</span>
          </div>
          <p className="text-ash" aria-live="polite">{questions} · {opened} in the {RANGES.find((r) => r.key === range)?.long}</p>
        </div>

        <div className="flex gap-3">
          <div className="flex flex-col justify-between text-[11px] text-ash" style={{ height: HEIGHT }} aria-hidden="true">{ticks.map((t) => <span key={t}>{t}</span>)}</div>
          <div className="min-w-0 flex-1">
            <div
              ref={wrapRef}
              role="group"
              tabIndex={0}
              aria-label={`${title}, ${RANGES.find((r) => r.key === range)?.long}, ${mode === "line" ? "line graph" : "bar chart"}. Use the left and right arrow keys to read each point.`}
              onPointerMove={move}
              onPointerDown={move}
              onPointerLeave={() => setHover(null)}
              onKeyDown={key}
              onBlur={() => setHover(null)}
              className="relative cursor-crosshair touch-pan-y rounded-lg outline-offset-4"
              style={{ height: HEIGHT }}
            >
              <svg width={width} height={HEIGHT} className="absolute inset-0 overflow-visible" aria-hidden="true">
                <defs>
                  <linearGradient id="gradBar" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor={COLOR_A} /><stop offset="1" stopColor="#b9a8ee" /></linearGradient>
                  <linearGradient id="gradAreaA" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={COLOR_A} stopOpacity="0.38" /><stop offset="1" stopColor={COLOR_A} stopOpacity="0" /></linearGradient>
                  <linearGradient id="gradAreaB" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={COLOR_B} stopOpacity="0.28" /><stop offset="1" stopColor={COLOR_B} stopOpacity="0" /></linearGradient>
                </defs>

                {ticks.map((t) => <line key={t} x1={0} x2={width} y1={y(t)} y2={y(t)} stroke="rgb(var(--c-fog))" strokeWidth={1} />)}

                {hover !== null && (
                  mode === "bars"
                    ? <rect x={hover * slot + 2} y={0} width={Math.max(0, slot - 4)} height={HEIGHT} rx={10} fill="rgb(var(--c-mist))" opacity={0.9} />
                    : <line x1={cx(hover)} x2={cx(hover)} y1={0} y2={HEIGHT} stroke="rgb(var(--c-ash))" strokeWidth={1} strokeDasharray="4 4" />
                )}

                {mode === "bars" && data.map((d, i) => {
                  const dim = hover !== null && hover !== i;
                  const hA = d.queries ? Math.max(6, HEIGHT - y(d.queries)) : 0;
                  const hB = d.document_views ? Math.max(6, HEIGHT - y(d.document_views)) : 0;
                  return (
                    <g key={d.date} opacity={dim ? 0.45 : 1} style={{ transition: "opacity 150ms" }}>
                      {hA > 0 && <rect x={cx(i) - bw - 1} y={HEIGHT - hA} width={bw} height={hA} rx={bw / 2} fill={i === last ? "url(#gradBar)" : COLOR_A} fillOpacity={i === last ? 1 : 0.78} style={{ transition: "y 450ms, height 450ms" }} />}
                      {hB > 0 && <rect x={cx(i) + 1} y={HEIGHT - hB} width={bw} height={hB} rx={bw / 2} fill={COLOR_B} style={{ transition: "y 450ms, height 450ms" }} />}
                    </g>
                  );
                })}

                {mode === "line" && n > 1 && (
                  <>
                    <path d={`${lineB}L${cx(last)},${HEIGHT}L${cx(0)},${HEIGHT}Z`} fill="url(#gradAreaB)" />
                    <path d={`${lineA}L${cx(last)},${HEIGHT}L${cx(0)},${HEIGHT}Z`} fill="url(#gradAreaA)" />
                    <path d={lineB} fill="none" stroke={COLOR_B} strokeWidth={2.5} strokeLinecap="round" />
                    <path d={lineA} fill="none" stroke={COLOR_A} strokeWidth={2.5} strokeLinecap="round" />
                  </>
                )}
                {mode === "line" && data.map((d, i) => {
                  const on = hover === i;
                  if (!showDots && !on) return null;
                  return (
                    <g key={d.date}>
                      <circle cx={cx(i)} cy={y(d.document_views)} r={on ? 6 : 3.5} fill="rgb(var(--c-surface))" stroke={COLOR_B} strokeWidth={2.5} />
                      <circle cx={cx(i)} cy={y(d.queries)} r={on ? 6 : 3.5} fill="rgb(var(--c-surface))" stroke={COLOR_A} strokeWidth={2.5} />
                    </g>
                  );
                })}
              </svg>

              {active && hover !== null && (
                <div
                  aria-hidden="true"
                  className="pointer-events-none absolute z-10 w-[200px] -translate-x-1/2 animate-pop rounded-xl border border-line bg-white px-3.5 py-2.5 text-[13px] shadow-soft"
                  style={{ left: tipLeft, top: tipTop }}
                >
                  <p className="font-bold">{rangeText(active.date)}</p>
                  <p className="mt-1.5 flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR_A }} /><span className="flex-1 text-graphite">{labels.a}</span><span className="font-bold">{active.queries}</span></p>
                  <p className="mt-1 flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: COLOR_B }} /><span className="flex-1 text-graphite">{labels.b}</span><span className="font-bold">{active.document_views}</span></p>
                </div>
              )}
            </div>

            <div className="mt-2 flex text-xs text-ash" aria-hidden="true">
              {data.map((d, i) => (
                <span key={d.date} className={`min-w-0 flex-1 whitespace-nowrap text-center ${hover === i ? "font-bold text-ink" : i === last ? "font-semibold text-ink" : ""}`}>{tickLabel(d.date, i)}</span>
              ))}
            </div>
          </div>
        </div>

        {peak === 0 && <p className="mt-3 text-[13px] text-ash">No activity in this period.</p>}

        <table className="sr-only">
          <caption>{title}, {RANGES.find((r) => r.key === range)?.long}</caption>
          <thead><tr><th>Period</th><th>{labels.a}</th><th>{labels.b}</th></tr></thead>
          <tbody>{data.map((d) => <tr key={d.date}><td>{rangeText(d.date)}</td><td>{d.queries}</td><td>{d.document_views}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}
