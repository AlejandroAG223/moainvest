import type { ReactNode } from "react";

export function PageIntro({ eyebrow, title, lead, children }: { eyebrow: string; title: ReactNode; lead?: ReactNode; children?: ReactNode }) {
  return (
    <section aria-labelledby="page-title" className="relative overflow-hidden border-b border-line">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 [background-image:radial-gradient(var(--color-line)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent)]"
      />
      <div className="relative mx-auto w-full max-w-6xl px-5 pt-16 pb-14 sm:px-8 sm:pt-24 sm:pb-20">
        <p className="hero-in eyebrow mb-5 flex items-center gap-3">
          <span aria-hidden className="h-px w-6 bg-brand" />
          {eyebrow}
        </p>
        <h1 id="page-title" className="hero-in max-w-4xl text-balance text-[2.5rem] leading-[1.04] font-semibold tracking-[-0.04em] sm:text-6xl" style={{ ["--i" as string]: 1 }}>
          {title}
        </h1>
        {lead && (
          <p className="hero-in mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-muted sm:text-xl" style={{ ["--i" as string]: 2 }}>
            {lead}
          </p>
        )}
        {children}
      </div>
    </section>
  );
}
