import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils/cn";

/** Compact lockup (symbol + wordmark) used in navigation. */
export function LogoLink({ invert = false, className }: { invert?: boolean; className?: string }) {
  return (
    <Link href="/" aria-label="MOAINVEST — inicio" className={cn("inline-flex shrink-0 items-center", className)}>
      <Image
        src={invert ? "/logo/moainvest-compact-white.png" : "/logo/moainvest-compact.png"}
        alt="MOAINVEST"
        width={844}
        height={110}
        preload
        className="h-6 w-auto sm:h-7"
      />
    </Link>
  );
}
