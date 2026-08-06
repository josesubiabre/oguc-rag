import { cn } from "@/lib/utils";

/** Isotipo geométrico de NormaObra: planos plegados, trazo lineal. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinejoin="round"
      strokeLinecap="round"
      className={cn("text-text-primary", className)}
      aria-hidden="true"
    >
      <path d="M8 13.5 19 8l10 5 11-5v26.5L29 40l-10-5-11 5Z" />
      <path d="M19 8v27" />
      <path d="M29 13v27" className="text-brand" stroke="currentColor" />
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
