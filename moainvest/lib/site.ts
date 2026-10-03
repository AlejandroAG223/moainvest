export const site = {
  name: "MOAINVEST",
  title: "MOAINVEST | Resumen, gráficas e informes de mercado",
  description: "Resumen del mercado, gráficas de precios en vivo e informes de activos con datos de Yahoo Finance.",
  tagline: "Personas — Conocimiento — Oportunidades",
  // Set NEXT_PUBLIC_SITE_URL in production so canonical / OG URLs are absolute.
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  locale: "es_CO",
};

export const mainNav = [
  { href: "/", label: "Resumen" },
  { href: "/graficas", label: "Gráficas" },
  { href: "/informe", label: "Informe" },
] as const;
