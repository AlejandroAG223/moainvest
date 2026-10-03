import { redirect } from "next/navigation";
import { BackendOffline } from "@/components/market/backend-offline";
import { Container } from "@/components/ui/section";
import { chartHref } from "@/lib/market";
import { getWatchlists } from "@/lib/market-server";

export default async function GraficasIndex() {
  const first = (await getWatchlists())?.[0];
  if (first) redirect(chartHref(first.slug, first.symbols[0].ticker));
  return (
    <Container className="py-16">
      <BackendOffline />
    </Container>
  );
}
