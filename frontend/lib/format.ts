// The API returns naive UTC timestamps (no "Z"). Treat them as UTC so they show in the viewer's local time.
export function parseDate(value: string): Date {
  const hasZone = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "";
  return parseDate(value).toLocaleString(undefined, { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  return parseDate(value).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function formatTime(value: string): string {
  return parseDate(value).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function dayLabel(value: string): string {
  const day = startOfDay(parseDate(value));
  const today = startOfDay(new Date());
  const diff = Math.round((today.getTime() - day.getTime()) / 86_400_000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  return day.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "short" });
}

/** Today / This week / Earlier, matching the chat history wireframe. */
export function chatBucket(value: string): "Today" | "This week" | "Earlier" {
  const day = startOfDay(parseDate(value)).getTime();
  const today = startOfDay(new Date()).getTime();
  if (day >= today) return "Today";
  if (day >= today - 6 * 86_400_000) return "This week";
  return "Earlier";
}

export function initial(name: string): string {
  return (name.trim()[0] ?? "?").toUpperCase();
}

export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] || name;
}

export function plural(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`;
}
