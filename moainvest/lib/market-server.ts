import type { Watchlist } from "./market";

const flaskUrl = process.env.FLASK_API_URL ?? "http://127.0.0.1:5000";

/** Watchlist registry from Flask; null when the backend is unreachable. */
export async function getWatchlists(): Promise<Watchlist[] | null> {
  try {
    const res = await fetch(`${flaskUrl}/api/watchlists`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return (await res.json()) as Watchlist[];
  } catch {
    return null;
  }
}
