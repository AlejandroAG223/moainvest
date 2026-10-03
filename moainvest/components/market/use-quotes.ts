"use client";

import { useEffect, useState } from "react";
import { QUOTE_POLL_MS, type Quote } from "@/lib/market";

/** Live quotes for a whole watchlist, refreshed every 15 s. */
export function useWatchlistQuotes(slug: string) {
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      fetch(`/api/watchlist/${encodeURIComponent(slug)}/quotes`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((data: Record<string, Quote>) => {
          if (!alive) return;
          setQuotes(data);
          setFailed(false);
        })
        .catch(() => alive && setFailed(true)); // keep the last values on screen
    load();
    const id = setInterval(load, QUOTE_POLL_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [slug]);

  return { quotes, failed };
}
