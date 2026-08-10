"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  CircleHelp,
  CircleUserRound,
  Code2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Scale,
  Search,
  Trash2,
} from "lucide-react";

import { BrandMark, BrandWordmark } from "@/components/brand";
import { CoberturaModal } from "@/components/cobertura";
import { LegalDisclaimerModal } from "@/components/legal-disclaimer";
import { Modal } from "@/components/ui/modal";
import { cn } from "@/lib/utils";

interface ConversationSummary {
  id: string;
  title: string;
}

interface AppSidebarProps {
  conversations: ConversationSummary[];
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
  onNewChat: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function AppSidebar({
  conversations,
  activeId,
  onSelectConversation,
  onDeleteConversation,
  onNewChat,
  mobileOpen,
  onMobileClose,
}: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [query, setQuery] = useState("");
  const [modal, setModal] = useState<"fuentes" | "como" | "legal" | null>(null);
  // Borrar es irreversible: el historial vive solo en este navegador y no hay
  // copia en servidor. Se pide un segundo clic en vez de abrir un diálogo,
  // que para una lista de consultas sería más molesto que protector.
  const [confirmando, setConfirmando] = useState<string | null>(null);

  useEffect(() => {
    if (!confirmando) return;
    const t = setTimeout(() => setConfirmando(null), 4000);
    return () => clearTimeout(t);
  }, [confirmando]);

  const recents = useMemo(
    () =>
      conversations.filter((c) =>
        c.title.toLowerCase().includes(query.trim().toLowerCase())
      ),
    [conversations, query]
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
              {recents.map((c) => (
                <li
                  key={c.id}
                  className={cn(
                    "flex items-center rounded-md border-b border-line-subtle transition-colors last:border-b-0 hover:bg-surface-hover",
                    c.id === activeId && "bg-surface-hover"
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSelectConversation(c.id)}
                    className={cn(
                      "flex h-11 min-w-0 flex-1 items-center gap-3 rounded-md px-1 text-left text-[14px] text-text-secondary transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand",
                      c.id === activeId && "text-text-primary"
                    )}
                  >
                    <MessageSquare className="h-4 w-4 shrink-0" aria-hidden="true" />
                    <span className="truncate">{c.title}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      if (confirmando === c.id) {
                        onDeleteConversation(c.id);
                        setConfirmando(null);
                      } else {
                        setConfirmando(c.id);
                      }
                    }}
                    // El estado se anuncia en el nombre accesible: quien no ve
                    // el cambio de icono debe enterarse igual de que el
                    // siguiente clic borra.
                    aria-label={
                      confirmando === c.id
                        ? `Confirmar eliminación de «${c.title}»`
                        : `Eliminar «${c.title}»`
                    }
                    className={cn(
                      "mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md transition-colors focus-visible:outline-2 focus-visible:outline-brand",
                      confirmando === c.id
                        ? "text-danger"
                        : "text-text-subtle hover:text-text-primary"
                    )}
                  >
                    {confirmando === c.id ? (
                      <Check className="h-4 w-4" aria-hidden="true" />
                    ) : (
                      <Trash2 className="h-4 w-4" aria-hidden="true" />
                    )}
                  </button>
                </li>
              ))}
              {recents.length === 0 && (
                <li className="px-1 py-2 text-[13px] text-text-subtle">
                  {conversations.length === 0
                    ? "Aún no tienes consultas guardadas"
                    : "Sin resultados"}
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
            label="Cobertura y fuentes"
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
            icon={<Scale className="h-4 w-4" aria-hidden="true" />}
            label="Aviso legal"
            collapsed={collapsed}
            onClick={() => setModal("legal")}
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
      <CoberturaModal
        open={modal === "fuentes"}
        onClose={() => setModal(null)}
      />

      <Modal
        title="Cómo funciona"
        open={modal === "como"}
        onClose={() => setModal(null)}
      >
        <ol className="list-decimal space-y-2 pl-5">
          <li>
            Tu pregunta se busca de dos maneras contra los 8.021 fragmentos del
            corpus: por significado y por coincidencia exacta de términos, como
            un número de artículo. Los dos resultados se combinan.
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

      <LegalDisclaimerModal
        open={modal === "legal"}
        onClose={() => setModal(null)}
      />

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
