import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["", "/graficas", "/informe"].map((r) => ({ url: `${site.url}${r}`, changeFrequency: "daily", priority: r === "" ? 1 : 0.7 }));
}
