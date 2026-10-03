"use client";

import { CandlestickSeries, ColorType, CrosshairMode, createChart, type IChartApi, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import { useEffect, useRef, useState } from "react";
import type { Candle, RangeOption } from "@/lib/market";

const UP = "#0f8a5f";
const DOWN = "#c8102e";

/** Candlestick chart (TradingView lightweight-charts) fed by /api/candles. */
export function PriceChart({ ticker, range }: { ticker: string; range: RangeOption }) {
  const box = useRef<HTMLDivElement>(null);
  const chart = useRef<IChartApi | null>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  // Result tagged with the request it belongs to, so a new ticker/range reads as "loading".
  const key = `${ticker}|${range.range}|${range.interval}`;
  const [result, setResult] = useState<{ key: string; state: "ready" | "empty" | "error" } | null>(null);
  const state = result?.key === key ? result.state : "loading";

  useEffect(() => {
    if (!box.current) return;
    const c = createChart(box.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "#ffffff" }, textColor: "#6b6b6b", fontFamily: "var(--font-geist-mono), monospace", attributionLogo: false },
      grid: { vertLines: { color: "#f3f2ef" }, horzLines: { color: "#f3f2ef" } },
      rightPriceScale: { borderColor: "#e6e4df" },
      timeScale: { borderColor: "#e6e4df", timeVisible: true, secondsVisible: false },
      crosshair: { mode: CrosshairMode.Normal },
    });
    series.current = c.addSeries(CandlestickSeries, { upColor: UP, downColor: DOWN, borderVisible: false, wickUpColor: UP, wickDownColor: DOWN });
    chart.current = c;
    return () => {
      c.remove();
      chart.current = null;
      series.current = null;
    };
  }, []);

  useEffect(() => {
    let alive = true;
    fetch(`/api/candles/${encodeURIComponent(ticker)}?range=${range.range}&interval=${range.interval}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((candles: Candle[]) => {
        if (!alive || !series.current) return;
        series.current.setData(candles.map((c) => ({ ...c, time: c.time as UTCTimestamp })));
        chart.current?.timeScale().fitContent();
        setResult({ key, state: candles.length ? "ready" : "empty" });
      })
      .catch(() => alive && setResult({ key, state: "error" }));
    return () => {
      alive = false;
    };
  }, [key, ticker, range]);

  return (
    <div className="relative h-[52svh] min-h-[320px] w-full overflow-hidden rounded-2xl border border-line bg-white">
      <div ref={box} className="absolute inset-2" role="img" aria-label={`Gráfico de velas de ${ticker}`} />
      {state !== "ready" && (
        <div className="absolute inset-0 grid place-items-center bg-white/80 text-sm text-muted" role="status">
          {state === "loading" && "Cargando datos de Yahoo Finance…"}
          {state === "empty" && "No hay datos para este rango."}
          {state === "error" && "No pudimos cargar el gráfico. Inténtalo de nuevo."}
        </div>
      )}
    </div>
  );
}
