"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  CircleHelp,
  CircleUserRound,
  Code2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
} from "lucide-react";

import { BrandMark, BrandWordmark } from "@/components/brand";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";

const CORPUS = [
  ["OGUC", "Ordenanza General de Urbanismo y Construcciones (marzo 2026)"],
  ["LGUC", "Ley General de Urbanismo y Construcciones (septiembre 2025)"],
  ["Ley N° 21.442", "Copropiedad Inmobiliaria"],
  ["DS 50", "Accesibilidad Universal"],
  ["Circulares DDU", "~250 circulares generales vigentes del MINVU"],
] as const;

/* Consultas de demostración para el estado vacío del historial.
   Cuando exista almacenamiento de conversaciones, esta lista se
   reemplaza por los datos reales. */
const DEMO_RECENTS = [
  "Permiso de obra menor",
  "Ruta accesible",
  "Bienes comunes",
  "Interpretación DDU",
];

interface AppSidebarProps {
  onSelectRecent: (topic: string) => void;
  onNewChat: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({
  onSelectRecent,
  onNewChat,
  mobileOpen,
  onMobileClose,
}: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<"fuentes" | "como" | null>(null);

  const recents = useMemo(
    () =>
      DEMO_RECENTS.filter((r) =>
        r.toLowerCase().includes(query.trim().toLowerCase())
      ),
    [query]
  );

  // Drawer mobile: cerrar con Escape y bloquear el scroll del body
  useEffect(() => {
    if (!mobileOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onMobileClose();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [mobileOpen, onMobileClose]);

  const content = (
    <div className="flex h-full flex-col p-4">
      {/* Marca + contraer */}
      <div className={cn("flex items-start gap-3", collapsed && "flex-col items-center")}>
        <BrandMark className={cn("shrink-0", collapsed ? "w-8 h-8" : "w-10 h-10")} />
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <BrandWordmark />
            <p className="mt-1 text-[13px] text-text-subtle">
              Normativa de construcción
            </p>
          </div>
        )}
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? "Expandir barra lateral" : "Contraer barra lateral"}
          className="hidden md:flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-line-subtle text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand"
        >
          {collapsed ? (
            <PanelLeftOpen className="h-4 w-4" aria-hidden="true" />
          ) : (
            <PanelLeftClose className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </div>

      {/* Nueva consulta */}
      <button
        type="button"
        onClick={onNewChat}
        className={cn(
          "mt-6 flex h-[52px] items-center justify-center gap-2 rounded-lg border border-brand text-brand transition-colors hover:bg-brand-soft focus-visible:outline-2 focus-visible:outline-brand",
          collapsed ? "w-full px-0" : "w-full px-4"
        )}
        aria-label="Nueva consulta"
      >
        <Plus className="h-4 w-4" aria-hidden="true" />
        {!collapsed && <span className="text-[15px]">Nueva consulta</span>}
      </button>

      {!collapsed && (
        <>
          {/* Buscador */}
          <label className="relative mt-4 block">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-subtle"
              aria-hidden="true"
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar consultas"
              aria-label="Buscar consultas"
              className="h-11 w-full rounded-lg border border-line-subtle bg-surface pl-9 pr-3 text-[14px] text-text-primary placeholder:text-text-subtle focus-visible:outline-2 focus-visible:outline-brand"
            />
          </label>

          {/* Recientes */}
          <div className="mt-6 min-h-0 flex-1 overflow-y-auto">
            <h2 className="px-1 text-[13px] font-medium text-text-subtle">
              Recientes
            </h2>
            <ul className="mt-2">
              {recents.map((topic) => (
                <li key={topic} className="border-b border-line-subtle last:border-b-0">
                  <button
                    type="button"
                    onClick={() => onSelectRecent(topic)}
                    className="flex h-11 w-full items-center gap-3 rounded-md px-1 text-left text-[14px] text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand"
                  >
                    <MessageSquare className="h-4 w-4 shrink-0" aria-hidden="true" />
                    <span className="truncate">{topic}</span>
                  </button>
                </li>
              ))}
              {recents.length === 0 && (
                <li className="px-1 py-2 text-[13px] text-text-subtle">
                  Sin resultados
                </li>
              )}
            </ul>
          </div>
        </>
      )}
      {collapsed && <div className="flex-1" />}

      {/* Navegación inferior */}
      <nav className="mt-auto pt-4" aria-label="Navegación secundaria">
        <ul className="space-y-1">
          <SidebarNavItem
            icon={<BookOpen className="h-4 w-4" aria-hidden="true" />}
            label="Fuentes normativas"
            collapsed={collapsed}
            onClick={() => setModal("fuentes")}
          />
          <SidebarNavItem
            icon={<CircleHelp className="h-4 w-4" aria-hidden="true" />}
            label="Cómo funciona"
            collapsed={collapsed}
            onClick={() => setModal("como")}
          />
          <SidebarNavItem
            icon={<Code2 className="h-4 w-4" aria-hidden="true" />}
            label="GitHub"
            collapsed={collapsed}
            href="https://github.com/josesubiabre/oguc-rag"
          />
        </ul>

        <div
          className={cn(
            "mt-4 flex items-center gap-2 border-t border-line-subtle pt-4",
            collapsed && "flex-col"
          )}
        >
          <div
            className={cn(
              "flex h-11 flex-1 items-center gap-2 rounded-lg border border-line-subtle px-3",
              collapsed && "w-full justify-center px-0"
            )}
          >
            <span
              className="h-2 w-2 shrink-0 rounded-full bg-brand"
              aria-hidden="true"
            />
            {!collapsed && (
              <span className="truncate text-[13px] text-text-secondary">
                Fuentes actualizadas
              </span>
            )}
          </div>
          <button
            type="button"
            aria-label="Cuenta"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line-subtle text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand"
          >
            <CircleUserRound className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </nav>
    </div>
  );

  return (
    <>
      {/* Escritorio / tablet */}
      <aside
        className={cn(
          "hidden md:block h-dvh shrink-0 border-r border-line bg-sidebar transition-[width]",
          collapsed ? "w-[76px]" : "w-[clamp(280px,22vw,380px)]"
        )}
      >
        {content}
      </aside>

      {/* Modales de navegación */}
      <Modal
        title="Fuentes normativas"
        open={modal === "fuentes"}
        onClose={() => setModal(null)}
      >
        <p>
          Norma responde exclusivamente a partir de estos cuerpos normativos
          oficiales:
        </p>
        <ul className="mt-3 space-y-2">
          {CORPUS.map(([name, desc]) => (
            <li key={name} className="flex gap-2">
              <span className="shrink-0 font-medium text-text-primary">{name}</span>
              <span>— {desc}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-[13px] text-text-subtle">
          Algunas circulares antiguas son escaneos sin texto extraíble y aún no
          forman parte del índice de búsqueda.
        </p>
      </Modal>

      <Modal
        title="Cómo funciona"
        open={modal === "como"}
        onClose={() => setModal(null)}
      >
        <ol className="list-decimal space-y-2 pl-5">
          <li>
            Tu pregunta se compara semánticamente contra los ~6.800 fragmentos
            indexados del corpus normativo.
          </li>
          <li>
            Los fragmentos más relevantes se entregan a un modelo de lenguaje,
            que redacta la respuesta usando únicamente ese contexto.
          </li>
          <li>
            Cada respuesta cita el documento y las páginas de origen, para que
            puedas verificar contra la fuente oficial.
          </li>
        </ol>
        <p className="mt-4">
          Si la normativa indexada no cubre tu pregunta, Norma lo dice en vez de
          inventar una respuesta.
        </p>
        <p className="mt-4 text-[13px] text-text-subtle">
          Herramienta informativa no oficial, sin afiliación con el MINVU. Las
          respuestas pueden contener errores: verifica siempre la normativa
          vigente y consulta a un profesional competente.
        </p>
      </Modal>

      {/* Drawer mobile */}
      {mobileOpen && (
        <div className="md:hidden" role="dialog" aria-modal="true" aria-label="Menú">
          <div
            className="fixed inset-0 z-40 bg-black/60"
            onClick={onMobileClose}
            aria-hidden="true"
          />
          <aside className="fixed inset-y-0 left-0 z-50 w-[300px] border-r border-line bg-sidebar">
            {content}
          </aside>
        </div>
      )}
    </>
  );
}

function SidebarNavItem({
  icon,
  label,
  collapsed,
  href,
  onClick,
}: {
  icon: React.ReactNode;
  label: string;
  collapsed: boolean;
  href?: string;
  onClick?: () => void;
}) {
  const className = cn(
    "flex h-11 w-full items-center gap-3 rounded-lg px-2 text-[14px] text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand",
    collapsed && "justify-center px-0"
  );
  if (href) {
    return (
      <li>
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className={className}
          aria-label={label}
        >
          {icon}
          {!collapsed && <span>{label}</span>}
        </a>
      </li>
    );
  }
  return (
    <li>
      <button
        type="button"
        className={className}
        aria-label={label}
        onClick={onClick}
      >
        {icon}
        {!collapsed && <span>{label}</span>}
      </button>
    </li>
  );
}
