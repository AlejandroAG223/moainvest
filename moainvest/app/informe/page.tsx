import type { Metadata } from "next";
import { BackendOffline } from "@/components/market/backend-offline";
import { ReportBuilder } from "@/components/market/report-builder";
import { PageIntro } from "@/components/layout/page-intro";
import { Container } from "@/components/ui/section";
import { getWatchlists } from "@/lib/market-server";

export const metadata: Metadata = {
  title: "Informe",
  description: "Genera el informe de activos de tus watchlists, revísalo y envíalo por correo.",
  alternates: { canonical: "/informe" },
};

export default async function InformePage() {
  const watchlists = await getWatchlists();
  return (
    <>
      <PageIntro
        eyebrow="Informe de activos"
        title={
          <>
            Tu informe, listo para <span className="accent">enviar</span>.
          </>
        }
        lead="Elige las watchlists, revisa el informe y envíalo por correo."
      />
      <Container className="py-12 sm:py-16">{watchlists ? <ReportBuilder watchlists={watchlists} /> : <BackendOffline />}</Container>
    </>
  );
}
