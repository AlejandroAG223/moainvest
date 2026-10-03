import type { ReactNode } from "react";
import { cn } from "@/lib/utils/cn";

type Tone = "white" | "mist" | "ink" | "brand";

const tones: Record<Tone, string> = {
  white: "bg-paper text-ink",
  mist: "bg-mist text-ink",
  ink: "bg-ink text-white",
  brand: "bg-brand-deep text-white",
};

export function Section({
  id,
  tone = "white",
  className,
  containerClassName,
  labelledBy,
  children,
}: {
  id?: string;
  tone?: Tone;
  className?: string;
  containerClassName?: string;
  labelledBy?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={labelledBy} className={cn("relative overflow-hidden py-20 sm:py-28", tones[tone], className)}>
      <div className={cn("mx-auto w-full max-w-6xl px-5 sm:px-8", containerClassName)}>{children}</div>
    </section>
  );
}

export function Container({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("mx-auto w-full max-w-6xl px-5 sm:px-8", className)}>{children}</div>;
}
