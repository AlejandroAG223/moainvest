import { ButtonLink } from "@/components/ui/button";
import { mainNav } from "@/lib/site";
import { LogoLink } from "./logo";
import { MobileNav } from "./mobile-nav";
import { NavLink } from "./nav-link";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/70 bg-white/85 backdrop-blur-md supports-[backdrop-filter]:bg-white/70">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-6 px-5 sm:px-8">
        <LogoLink />
        <nav aria-label="Menú principal" className="hidden md:block">
          <ul className="flex items-center gap-7 text-[0.92rem]">
            {mainNav.map((item) => (
              <li key={item.href}>
                <NavLink href={item.href} label={item.label} />
              </li>
            ))}
          </ul>
        </nav>
        <div className="hidden items-center gap-2 md:flex">
          <ButtonLink href="/informe" size="sm">
            Generar informe
          </ButtonLink>
        </div>
        <MobileNav />
      </div>
    </header>
  );
}
