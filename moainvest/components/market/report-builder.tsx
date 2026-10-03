"use client";

import { Eye, Send } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { Watchlist } from "@/lib/market";
import { cn } from "@/lib/utils/cn";

type Status = { text: string; error?: boolean } | null;

export function ReportBuilder({ watchlists }: { watchlists: Watchlist[] }) {
  const [selected, setSelected] = useState<string[]>(watchlists.map((w) => w.slug));
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<Status>(null);

  const toggle = (slug: string) => setSelected((s) => (s.includes(slug) ? s.filter((x) => x !== slug) : [...s, slug]));

  function requireSelection() {
    if (selected.length) return true;
    setStatus({ text: "Selecciona al menos una watchlist.", error: true });
    return false;
  }

  function preview() {
    if (!requireSelection()) return;
    setStatus(null);
    setLoadingPreview(true);
    setPreviewUrl(`/api/report/preview?watchlists=${encodeURIComponent(selected.join(","))}&t=${Date.now()}`);
  }

  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!requireSelection()) return;
    const to = email.trim();
    setSending(true);
    setStatus({ text: `Enviando informe a ${to}…` });
    try {
      const res = await fetch("/api/email/send-assets-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ to, watchlists: selected }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `Error ${res.status}`);
      setStatus({ text: `Informe enviado a ${to}.` });
    } catch (err) {
      setStatus({ text: `No se pudo enviar el informe: ${(err as Error).message}`, error: true });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[22rem_1fr]">
      <div className="space-y-6 lg:sticky lg:top-24 lg:h-fit">
        <fieldset className="rounded-2xl border border-line bg-white p-6">
          <legend className="eyebrow px-1">01 · Watchlists incluidas</legend>
          <div className="mt-2 space-y-2">
            {watchlists.map((w) => {
              const on = selected.includes(w.slug);
              return (
                <label
                  key={w.slug}
                  className={cn(
                    "flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-sm transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-brand",
                    on ? "border-ink/30 bg-mist" : "border-line hover:border-ink/30",
                  )}
                >
                  <input type="checkbox" checked={on} onChange={() => toggle(w.slug)} className="size-4 accent-[#c8102e]" />
                  <span aria-hidden>{w.icon}</span>
                  <span className="flex-1 font-medium">{w.name}</span>
                  <span className="font-mono text-xs text-muted">{w.symbols.length}</span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <div className="rounded-2xl border border-line bg-white p-6">
          <p className="eyebrow">02 · Revisa</p>
          <Button variant="secondary" className="mt-4 w-full" onClick={preview} disabled={loadingPreview}>
            <Eye className="size-4" aria-hidden />
            {loadingPreview ? "Generando informe…" : "Ver informe"}
          </Button>
        </div>

        <form onSubmit={send} className="rounded-2xl border border-line bg-white p-6">
          <label htmlFor="report-email" className="eyebrow block">
            03 · Envía por correo
          </label>
          <input
            id="report-email"
            type="email"
            required
            autoComplete="email"
            placeholder="destino@ejemplo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-4 w-full rounded-xl border border-line bg-white px-4 py-3 text-base outline-none transition-colors placeholder:text-muted/70 focus:border-ink"
          />
          <Button type="submit" className="mt-3 w-full" disabled={sending}>
            <Send className="size-4" aria-hidden />
            {sending ? "Enviando…" : "Enviar por correo"}
          </Button>
        </form>

        {status && (
          <p role={status.error ? "alert" : "status"} className={cn("rounded-xl px-4 py-3 text-sm", status.error ? "bg-brand-soft text-brand-deep" : "bg-mist text-ink")}>
            {status.text}
          </p>
        )}
      </div>

      <div className="min-h-[60svh] overflow-hidden rounded-3xl border border-line bg-mist">
        {previewUrl ? (
          <iframe
            key={previewUrl}
            src={previewUrl}
            title="Vista previa del informe"
            onLoad={() => setLoadingPreview(false)}
            className="h-[80svh] w-full bg-white"
          />
        ) : (
          <div className="grid h-full min-h-[60svh] place-content-center p-8 text-center">
            <p className="text-lg font-medium">La vista previa aparecerá aquí.</p>
            <p className="mt-1 text-sm text-muted">Elige las watchlists y pulsa «Ver informe».</p>
          </div>
        )}
      </div>
    </div>
  );
}
