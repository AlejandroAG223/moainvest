/** Shapes returned by the Flask API (app/controllers/api.py). */

export interface Quote {
  symbol: string;
  name: string;
  price: number | null;
  previous_close: number | null;
  change: number | null;
  change_percent: number | null;
  currency: string | null;
  is_up: boolean;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistSymbol {
  ticker: string;
  name: string;
}

export interface Watchlist {
  slug: string;
  name: string;
  icon: string;
  symbols: WatchlistSymbol[];
}

export const QUOTE_POLL_MS = 15_000;

export const ranges = [
  { label: "1D", range: "5d", interval: "15m" },
  { label: "5D", range: "5d", interval: "1h" },
  { label: "1M", range: "1mo", interval: "1d" },
  { label: "6M", range: "6mo", interval: "1d" },
  { label: "1A", range: "1y", interval: "1d" },
  { label: "5A", range: "5y", interval: "1wk" },
  { label: "Todo", range: "max", interval: "1mo" },
] as const;

export type RangeOption = (typeof ranges)[number];

export function fmtPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  // "always" so 4-digit prices group too (7.722,72), matching the larger ones.
  return value.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 4, useGrouping: "always" } as Intl.NumberFormatOptions);
}

export function fmtPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function fmtChange(q: Pick<Quote, "change" | "change_percent">): string {
  if (q.change === null || q.change_percent === null) return "—";
  const sign = q.change >= 0 ? "+" : "";
  return `${sign}${fmtPrice(q.change)} (${sign}${q.change_percent.toFixed(2)}%)`;
}

export function chartHref(slug: string, ticker: string) {
  return `/graficas/${slug}/${encodeURIComponent(ticker)}`;
}
