import { ArrowRight, CandlestickChart, FileText } from "lucide-react";
import Link from "next/link";
import { BackendOffline } from "@/components/market/backend-offline";
import { MarketOverview } from "@/components/market/market-overview";
import { PageIntro } from "@/components/layout/page-intro";
import { Container } from "@/components/ui/section";
import { getWatchlists } from "@/lib/market-server";

const shortcuts = [
  { href: "/graficas", icon: CandlestickChart, title: "Gráficas", body: "Velas en vivo de cada activo, por watchlist y con rangos de 1 día a todo el histórico." },
  { href: "/informe", icon: FileText, title: "Informe", body: "Elige tus watchlists, revisa el informe de activos y envíalo por correo." },
];

export default async function ResumenPage() {
  const watchlists = await getWatchlists();
  const overview = watchlists?.find((w) => w.slug === "overview") ?? watchlists?.[0];

  return (
    <>
      <PageIntro
        eyebrow="Mercado en vivo · Yahoo Finance"
        title={
          <>
            Resumen del <span className="accent">mercado</span>.
          </>
        }
        lead="Índices, cripto y divisas de un vistazo. Los precios se actualizan cada 15 segundos."
      />
      <Container className="py-12 sm:py-16">
        {overview ? <MarketOverview watchlist={overview} /> : <BackendOffline />}

        <ul className="mt-16 grid gap-4 md:grid-cols-2">
          {shortcuts.map(({ href, icon: Icon, title, body }, i) => (
            <li key={href} data-reveal style={{ ["--i" as string]: i }}>
              <Link href={href} className="group flex h-full items-start gap-5 rounded-2xl border border-line bg-mist p-6 transition-colors hover:border-brand/40 sm:p-8">
                <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-white text-brand transition-colors group-hover:bg-brand group-hover:text-white">
                  <Icon className="size-5" strokeWidth={1.6} aria-hidden />
                </span>
                <span>
                  <span className="flex items-center gap-2 text-xl font-semibold tracking-tight">
                    {title}
                    <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
                  </span>
                  <span className="mt-1.5 block leading-relaxed text-muted">{body}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </Container>
    </>
  );
}
