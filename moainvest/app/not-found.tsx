import { ButtonLink } from "@/components/ui/button";
import { Container } from "@/components/ui/section";

export default function NotFound() {
  return (
    <Container className="grid min-h-[60svh] place-content-center py-20 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-4 text-4xl font-semibold tracking-tight sm:text-5xl">
        Este camino todavía no <span className="accent">existe</span>.
      </h1>
      <p className="mt-4 text-lg text-muted">Quizá sea una buena idea para construir juntos.</p>
      <div className="mt-8">
        <ButtonLink href="/">Volver al inicio</ButtonLink>
      </div>
    </Container>
  );
}
