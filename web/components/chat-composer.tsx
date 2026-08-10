"use client";

import { forwardRef, useImperativeHandle, useSyncExternalStore } from "react";
import { ArrowUp, BookOpen } from "lucide-react";

import { Textarea } from "@/components/ui/textarea";
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea";
import { cn } from "@/lib/utils";

/* En móvil el placeholder largo se quiebra a dos líneas y el composer
   compacto solo muestra una: usamos una versión corta bajo 768px. */
function subscribeToViewport(callback: () => void) {
  const media = window.matchMedia("(max-width: 767px)");
  media.addEventListener("change", callback);
  return () => media.removeEventListener("change", callback);
}

function useIsMobile() {
  return useSyncExternalStore(
    subscribeToViewport,
    () => window.matchMedia("(max-width: 767px)").matches,
    () => false
  );
}

export interface ChatComposerHandle {
  focus: () => void;
  resetHeight: () => void;
}

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onOpenSources: () => void;
  loading: boolean;
}

export const ChatComposer = forwardRef<ChatComposerHandle, ChatComposerProps>(
  function ChatComposer(
    { value, onChange, onSubmit, onOpenSources, loading },
    ref
  ) {
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
      minHeight: 48,
      maxHeight: 240,
    });

    useImperativeHandle(ref, () => ({
      focus: () => textareaRef.current?.focus(),
      resetHeight: () => adjustHeight(true),
    }));

    const isMobile = useIsMobile();
    const canSend = value.trim().length > 0 && !loading;

    return (
      <div className="w-full rounded-2xl border border-line bg-surface shadow-[0_8px_30px_rgba(0,0,0,0.25)]">
        <Textarea
          ref={textareaRef}
          value={value}
          maxLength={500}
          onChange={(e) => {
            onChange(e.target.value);
            adjustHeight();
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (canSend) onSubmit();
            }
          }}
          placeholder={
            isMobile
              ? "Pregúntale a Norma…"
              : "Pregúntale a Norma sobre normativa de construcción…"
          }
          aria-label="Pregunta sobre normativa de construcción"
          className={cn(
            "min-h-[48px] w-full resize-none border-none bg-transparent px-4 py-3",
            "text-[16px] leading-relaxed text-text-primary",
            "placeholder:text-text-subtle placeholder:text-[16px]",
            "focus:outline-none focus-visible:ring-0 focus-visible:ring-offset-0"
          )}
          style={{ overflow: "hidden" }}
        />

        <div className="flex items-center justify-between px-2 pb-2">
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onOpenSources}
              aria-label="Ver qué normativa cubre Norma"
              className="flex h-9 items-center gap-2 rounded-lg px-2.5 text-[13px] text-text-secondary transition-colors hover:bg-surface-hover hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand"
            >
              <BookOpen className="h-4 w-4" aria-hidden="true" />
              Fuentes
            </button>
          </div>

          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSend}
            aria-label="Enviar consulta"
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full bg-brand text-white transition-colors",
              "hover:bg-brand-hover focus-visible:outline-2 focus-visible:outline-brand",
              !canSend && "cursor-not-allowed opacity-40 hover:bg-brand"
            )}
          >
            <ArrowUp className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    );
  }
);
