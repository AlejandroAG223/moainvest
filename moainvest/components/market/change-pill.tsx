import { cn } from "@/lib/utils/cn";

export function changeTone(value: number | null | undefined) {
  if (value === null || value === undefined) return "text-muted";
  return value >= 0 ? "text-up" : "text-brand";
}

export function ChangePill({ value, children, className }: { value: number | null | undefined; children: React.ReactNode; className?: string }) {
  const tone = value === null || value === undefined ? "bg-mist text-muted" : value >= 0 ? "bg-up-soft text-up" : "bg-brand-soft text-brand-deep";
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 font-mono text-xs tabular-nums", tone, className)}>{children}</span>;
}
