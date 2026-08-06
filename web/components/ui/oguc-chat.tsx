"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BouncingDots } from "@/components/ui/bouncing-dots";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  ArrowUpIcon,
  BookOpenText,
  FileText,
  Home,
  Ruler,
} from "lucide-react";

interface UseAutoResizeTextareaProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({
  minHeight,
  maxHeight,
}: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      );
      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) textarea.style.height = `${minHeight}px`;
  }, [minHeight]);

  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [adjustHeight]);

  return { textareaRef, adjustHeight };
}

interface Source {
  source: string;
  pages: number[];
}

interface Answer {
  answer: string;
  sources: Source[];
}

export function OgucChat() {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  });

  const ask = useCallback(
    async (question: string) => {
      const q = question.trim();
      if (!q || loading) return;
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        const r = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail ?? "Error inesperado");
        setResult(data);
        setValue("");
        adjustHeight(true);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error inesperado");
      } finally {
        setLoading(false);
        textareaRef.current?.focus();
      }
    },
    [loading, adjustHeight, textareaRef]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ask(value);
    }
  };

  return (
    <div className="flex flex-col items-center w-full max-w-4xl mx-auto p-4 space-y-8">
      <h1 className="text-4xl font-bold text-white text-center tracking-tight">
        ¿Qué quieres saber de la OGUC?
      </h1>

      <div className="w-full max-w-2xl">
        <div className="relative bg-neutral-900 rounded-xl border border-neutral-800">
          <div className="overflow-y-auto">
            <Textarea
              ref={textareaRef}
              value={value}
              maxLength={500}
              onChange={(e) => {
                setValue(e.target.value);
                adjustHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Pregúntale a la Ordenanza General de Urbanismo y Construcciones..."
              className={cn(
                "w-full px-4 py-3",
                "resize-none",
                "bg-transparent",
                "border-none",
                "text-white text-sm",
                "focus:outline-none",
                "focus-visible:ring-0 focus-visible:ring-offset-0",
                "placeholder:text-neutral-500 placeholder:text-sm",
                "min-h-[60px]"
              )}
              style={{ overflow: "hidden" }}
            />
          </div>

          <div className="flex items-center justify-between p-3">
            <span className="text-xs text-neutral-600 pl-1">
              Enter para enviar · Shift+Enter para salto de línea
            </span>
            <button
              type="button"
              onClick={() => ask(value)}
              disabled={loading}
              className={cn(
                "px-1.5 py-1.5 rounded-lg text-sm transition-colors border border-zinc-700 hover:border-zinc-600 hover:bg-zinc-800 flex items-center justify-between gap-1",
                value.trim() ? "bg-white text-black" : "text-zinc-400",
                loading && "opacity-50 cursor-wait"
              )}
            >
              <ArrowUpIcon
                className={cn(
                  "w-4 h-4",
                  value.trim() ? "text-black" : "text-zinc-400"
                )}
              />
              <span className="sr-only">Enviar</span>
            </button>
          </div>
        </div>

        <div className="flex items-center justify-center flex-wrap gap-3 mt-4">
          <ActionButton
            icon={<FileText className="w-4 h-4" />}
            label="¿Qué es un permiso de obra menor?"
            onClick={ask}
          />
          <ActionButton
            icon={<Ruler className="w-4 h-4" />}
            label="¿Altura mínima de una baranda?"
            onClick={ask}
          />
          <ActionButton
            icon={<Home className="w-4 h-4" />}
            label="¿Distancia mínima con el vecino?"
            onClick={ask}
          />
          <ActionButton
            icon={<BookOpenText className="w-4 h-4" />}
            label="¿Necesito permiso para ampliar mi casa?"
            onClick={ask}
          />
        </div>
      </div>

      {(loading || result || error) && (
        <div className="w-full max-w-2xl">
          <div
            className={cn(
              "bg-neutral-900 border border-neutral-800 rounded-xl p-5 text-sm leading-relaxed text-neutral-100 whitespace-pre-wrap",
              loading && "text-neutral-400"
            )}
          >
            {loading && (
              <BouncingDots
                className="w-2 h-2 bg-neutral-500"
                animate={{ y: [0, -8, 0] }}
                message="Buscando en la normativa…"
                messagePlacement="right"
              />
            )}
            {error && `⚠️ ${error}`}
            {result && (
              <>
                {result.answer}
                <div className="text-xs text-zinc-400 mt-4">
                  Fuentes:{" "}
                  {result.sources
                    .map((s) => `${s.source} (págs. ${s.pages.join(", ")})`)
                    .join(" · ")}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

interface ActionButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: (question: string) => void;
}

function ActionButton({ icon, label, onClick }: ActionButtonProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(label)}
      className="flex items-center gap-2 px-4 py-2 bg-neutral-900 hover:bg-neutral-800 rounded-full border border-neutral-800 text-neutral-400 hover:text-white transition-colors"
    >
      {icon}
      <span className="text-xs">{label}</span>
    </button>
  );
}
