import { notFound, redirect } from "next/navigation";
import { chartHref } from "@/lib/market";
import { getWatchlists } from "@/lib/market-server";

export default async function WatchlistIndex({ params }: PageProps<"/graficas/[slug]">) {
  const { slug } = await params;
  const watchlists = await getWatchlists();
  if (!watchlists) redirect("/graficas");
  const w = watchlists.find((x) => x.slug === slug);
  if (!w) notFound();
  redirect(chartHref(w.slug, w.symbols[0].ticker));
}
