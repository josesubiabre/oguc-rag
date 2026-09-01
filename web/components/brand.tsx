import { cn } from "@/lib/utils";

/** Isotipo de NormaObra: tres planos rectangulares superpuestos. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={cn("text-text-primary", className)}
      role="img"
      aria-label="NormaObra"
    >
      {/* Plano posterior */}
      <path
        d="M8 18.5 28 8.5V43.5L8 53.5V18.5Z"
        stroke="currentColor"
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Plano central: acento de marca */}
      <path
        d="M19 23.5 39 13.5V48.5L19 58.5V23.5Z"
        stroke="var(--brand)"
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Plano frontal */}
      <path
        d="M31.5 27 54 15.75V50.75L31.5 62V27Z"
        stroke="currentColor"
        strokeWidth="2.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function BrandWordmark({ className }: { className?: string }) {
  return (
    <span className={cn("font-semibold tracking-tight text-[26px] leading-none", className)}>
      <span className="text-text-primary">Norma</span>
      <span className="text-brand">Obra</span>
    </span>
  );
}
