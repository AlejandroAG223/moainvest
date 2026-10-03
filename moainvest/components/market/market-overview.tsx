"use client";

import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { chartHref, fmtPercent, fmtPrice, type Watchlist } from "@/lib/market";
import { ChangePill } from "./change-pill";
import { Sparkline } from "./sparkline";
import { useWatchlistQuotes } from "./use-quotes";

export function MarketOverview({ watchlist }: { watchlist: Watchlist }) {
  const { quotes, failed } = useWatchlistQuotes(watchlist.slug);

  return (
    <>
      {failed && (
        <p role="status" className="mb-6 rounded-xl bg-brand-soft px-4 py-3 text-sm text-brand-deep">
          No pudimos actualizar los precios. Se muestran los últimos valores disponibles.
        </p>
      )}
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {watchlist.symbols.map((s, i) => {
          const q = quotes[s.ticker];
          return (
            <li key={s.ticker} data-reveal style={{ ["--i" as string]: i }}>
              <Link
                href={chartHref(watchlist.slug, s.ticker)}
                className="group block h-full rounded-2xl border border-line bg-white p-6 transition-[border-color,box-shadow,transform] duration-500 ease-out-soft hover:-translate-y-1 hover:border-ink/20 hover:shadow-[0_24px_48px_-30px_rgba(23,23,23,.4)]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-lg font-semibold tracking-tight">{s.name}</p>
                    <p className="font-mono text-xs tracking-[0.1em] text-muted">{s.ticker}</p>
                  </div>
                  <ArrowUpRight className="size-5 shrink-0 text-muted transition-[color,transform] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-brand" aria-hidden />
                </div>
                <div className="mt-5 flex items-end justify-between gap-3">
                  <p className="font-mono text-2xl font-medium tabular-nums tracking-tight" aria-live="polite">
                    {q ? fmtPrice(q.price) : <span className="inline-block h-7 w-28 animate-pulse rounded bg-mist align-middle" />}
                    {q?.currency && <span className="ml-1.5 text-xs text-muted">{q.currency}</span>}
                  </p>
                  <ChangePill value={q?.change_percent}>{fmtPercent(q?.change_percent)}</ChangePill>
                </div>
                <div className="mt-4">
                  <Sparkline ticker={s.ticker} />
                </div>
                <p className="mt-2 text-xs text-muted">Último mes · ver gráfica</p>
              </Link>
            </li>
          );
        })}
      </ul>
    </>
  );
}
