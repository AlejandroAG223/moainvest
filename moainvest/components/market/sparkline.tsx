"use client";

import { useEffect, useState } from "react";
import type { Candle } from "@/lib/market";

/** One-month closing-price line, drawn as plain SVG (no chart library). */
export function Sparkline({ ticker }: { ticker: string }) {
  const [closes, setCloses] = useState<number[] | null>(null);

  useEffect(() => {
    let alive = true;
    fetch(`/api/candles/${encodeURIComponent(ticker)}?range=1mo&interval=1d`)
      .then((r) => (r.ok ? r.json() : []))
      .then((c: Candle[]) => alive && setCloses(c.map((x) => x.close)))
      .catch(() => alive && setCloses([]));
    return () => {
      alive = false;
    };
  }, [ticker]);

  const gid = `spark-${ticker.replace(/[^a-z0-9]/gi, "")}`;
  const W = 240;
  const H = 64;
  if (!closes) return <div className="h-16 animate-pulse rounded-lg bg-mist" aria-hidden />;
  if (closes.length < 2) return <div className="h-16" aria-hidden />;

  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  const pts = closes.map((v, i) => [(i / (closes.length - 1)) * W, H - 4 - ((v - min) / span) * (H - 8)]);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const up = closes[closes.length - 1] >= closes[0];
  const color = up ? "var(--color-up)" : "var(--color-brand)";

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-16 w-full" aria-hidden>
      <defs>
        <linearGradient id={gid} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.18" />
          <stop offset="1" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${line} L${W} ${H} L0 ${H} Z`} fill={`url(#${gid})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="1.75" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  );
}
