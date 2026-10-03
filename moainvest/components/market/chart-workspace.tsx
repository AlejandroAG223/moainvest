"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { chartHref, fmtChange, fmtPercent, fmtPrice, QUOTE_POLL_MS, ranges, type Quote, type Watchlist } from "@/lib/market";
import { cn } from "@/lib/utils/cn";
import { ChangePill, changeTone } from "./change-pill";
import { PriceChart } from "./price-chart";
import { useWatchlistQuotes } from "./use-quotes";

export function ChartWorkspace({ watchlists, active, ticker }: { watchlists: Watchlist[]; active: Watchlist; ticker: string }) {
  const symbol = active.symbols.find((s) => s.ticker === ticker)!;
  const { quotes } = useWatchlistQuotes(active.slug);
  const [range, setRange] = useState<(typeof ranges)[number]>(ranges[2]);
  const [loaded, setLoaded] = useState<{ ticker: string; quote: Quote } | null>(null);
  const quote = loaded?.ticker === ticker ? loaded.quote : null;

  // Header quote for the selected symbol (its own poll, as in the original panel).
  useEffect(() => {
    let alive = true;
    const load = () =>
      fetch(`/api/quote/${encodeURIComponent(ticker)}`)
        .then((r) => (r.ok ? r.json() : Promise.reject()))
        .then((q: Quote) => alive && setLoaded({ ticker, quote: q }))
        .catch(() => {});
    load();
    const id = setInterval(load, QUOTE_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [ticker]);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[18rem_1fr]">
      <aside aria-label="Watchlists" className="min-w-0 lg:sticky lg:top-24 lg:h-fit">
        <nav aria-label="Elegir watchlist" className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0">
          {watchlists.map((w) => (
            <Link
              key={w.slug}
              href={chartHref(w.slug, w.symbols[0].ticker)}
              aria-current={w.slug === active.slug ? "page" : undefined}
              className={cn(
                "shrink-0 rounded-full border px-4 py-2 text-sm whitespace-nowrap transition-colors lg:rounded-xl",
                w.slug === active.slug ? "border-ink bg-ink text-white" : "border-line bg-white text-ink/80 hover:border-ink/40",
              )}
            >
              <span aria-hidden className="mr-1.5">
                {w.icon}
              </span>
              {w.name}
            </Link>
          ))}
        </nav>

        <ul className="mt-4 divide-y divide-line overflow-hidden rounded-2xl border border-line bg-white" aria-label={`Símbolos de ${active.name}`}>
          {active.symbols.map((s) => {
            const q = quotes[s.ticker];
            const current = s.ticker === ticker;
            return (
              <li key={s.ticker}>
                <Link
                  href={chartHref(active.slug, s.ticker)}
                  aria-current={current ? "page" : undefined}
                  className={cn("flex items-center justify-between gap-3 px-4 py-3 transition-colors", current ? "bg-mist" : "hover:bg-mist/60")}
                >
                  <span className="min-w-0">
                    <span className={cn("block truncate text-sm font-medium", current && "text-brand")}>{s.name}</span>
                    <span className="block font-mono text-[0.68rem] tracking-[0.08em] text-muted">{s.ticker}</span>
                  </span>
                  <span className="text-right font-mono text-xs tabular-nums">
                    <span className="block">{fmtPrice(q?.price)}</span>
                    <span className={cn("block", changeTone(q?.change_percent))}>{fmtPercent(q?.change_percent)}</span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </aside>

      <section aria-labelledby="symbol-title" className="min-w-0">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="eyebrow">{active.name}</p>
            <h1 id="symbol-title" className="mt-2 text-3xl font-semibold tracking-[-0.03em] sm:text-4xl">
              {symbol.name} <span className="font-mono text-base font-normal tracking-[0.08em] text-muted">{symbol.ticker}</span>
            </h1>
          </div>
          <div className="text-right" aria-live="polite">
            <p className="font-mono text-3xl font-medium tabular-nums tracking-tight">
              {fmtPrice(quote?.price)}
              {quote?.currency && <span className="ml-1.5 text-sm text-muted">{quote.currency}</span>}
            </p>
            <ChangePill value={quote?.change} className="mt-1">
              {quote ? fmtChange(quote) : "—"}
            </ChangePill>
          </div>
        </header>

        <div role="group" aria-label="Rango de tiempo" className="mt-6 flex flex-wrap gap-1.5">
          {ranges.map((r) => (
            <button
              key={r.label}
              type="button"
              aria-pressed={r.label === range.label}
              onClick={() => setRange(r)}
              className={cn(
                "rounded-full px-3.5 py-1.5 font-mono text-xs transition-colors",
                r.label === range.label ? "bg-brand text-white" : "bg-mist text-ink/80 hover:bg-line",
              )}
            >
              {r.label}
            </button>
          ))}
        </div>

        <div className="mt-4">
          <PriceChart ticker={ticker} range={range} />
        </div>
        <p className="mt-3 text-xs text-muted">Datos de Yahoo Finance. Los precios se actualizan cada 15 segundos y pueden tener retraso.</p>
      </section>
    </div>
  );
}
