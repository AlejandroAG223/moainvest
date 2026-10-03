import Image from "next/image";
import Link from "next/link";
import { mainNav, site } from "@/lib/site";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-5 py-12 sm:px-8 md:flex-row md:items-start md:justify-between">
        <div>
          <Image src="/logo/moainvest-compact.png" alt="MOAINVEST" width={844} height={110} className="h-6 w-auto" />
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted">
            Datos de mercado de Yahoo Finance. Pueden tener retraso y no constituyen asesoría financiera.
          </p>
        </div>
        <nav aria-label="Navegación del pie de página">
          <ul className="flex gap-6 text-sm">
            {mainNav.map((item) => (
              <li key={item.href}>
                <Link href={item.href} className="text-ink/80 transition-colors hover:text-brand">
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="border-t border-line">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-5 py-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p>© 2026 {site.name}</p>
          <p className="font-mono tracking-[0.14em] uppercase">{site.tagline}</p>
        </div>
      </div>
    </footer>
  );
}
