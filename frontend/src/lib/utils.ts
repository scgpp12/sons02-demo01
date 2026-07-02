import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** 円フォーマット（例: 600000 → ¥600,000） */
export function yen(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return "¥" + value.toLocaleString("ja-JP");
}

/** パーセント表示（例: 16.7 → 16.7%） */
export function percent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return `${value}%`;
}

/** YYYY-MM-DD（日付のみ） */
export function fmtDate(value: string | null | undefined): string {
  if (!value) return "-";
  return value.slice(0, 10);
}

/** YYYY-MM（対象月） */
export function fmtMonth(value: string | null | undefined): string {
  if (!value) return "-";
  return value.slice(0, 7);
}

/** 今月の月初日 YYYY-MM-01 */
export function thisMonthStart(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}
