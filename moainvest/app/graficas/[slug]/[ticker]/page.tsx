import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { ChartWorkspace } from "@/components/market/chart-workspace";
import { Container } from "@/components/ui/section";
import { getWatchlists } from "@/lib/market-server";

async function resolve(params: PageProps<"/graficas/[slug]/[ticker]">["params"]) {
  const { slug, ticker: raw } = await params;
  const ticker = decodeURIComponent(raw);
  const watchlists = await getWatchlists();
  if (!watchlists) return { watchlists: null } as const;
  const active = watchlists.find((w) => w.slug === slug);
  const symbol = active?.symbols.find((s) => s.ticker === ticker);
  return { watchlists, active, symbol, ticker } as const;
}

export async function generateMetadata({ params }: PageProps<"/graficas/[slug]/[ticker]">): Promise<Metadata> {
  const { symbol } = await resolve(params);
  return { title: symbol ? `${symbol.name} · Gráficas` : "Gráficas", robots: { index: false } };
}

export default async function ChartPage({ params }: PageProps<"/graficas/[slug]/[ticker]">) {
  const r = await resolve(params);
  if (!r.watchlists) redirect("/graficas");
  if (!r.active || !r.symbol) notFound();
  return (
    <Container className="py-10 sm:py-14">
      <ChartWorkspace watchlists={r.watchlists} active={r.active} ticker={r.ticker} />
    </Container>
  );
}
