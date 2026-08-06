"use client";

import { useCallback, useRef, useState } from "react";
import { Menu } from "lucide-react";

import { AppSidebar } from "@/components/app-sidebar";
import { ChatComposer, ChatComposerHandle } from "@/components/chat-composer";
import { BouncingDots } from "@/components/ui/bouncing-dots";
import { cn } from "@/lib/utils";

interface Source {
  source: string;
  pages: number[];
}

interface Answer {
  answer: string;
  sources: Source[];
}

export function NormaObraApp() {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Answer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const composerRef = useRef<ChatComposerHandle>(null);

  const ask = useCallback(async () => {
    const question = value.trim();
    if (!question || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail ?? "Error inesperado");
      setResult(data);
      setValue("");
      composerRef.current?.resetHeight();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setLoading(false);
      composerRef.current?.focus();
    }
  }, [value, loading]);

  const startNewChat = useCallback(() => {
    setValue("");
    setResult(null);
    setError(null);
    setMobileOpen(false);
    composerRef.current?.resetHeight();
    composerRef.current?.focus();
  }, []);

  const selectRecent = useCallback((topic: string) => {
    setValue(topic);
    setMobileOpen(false);
    composerRef.current?.focus();
  }, []);

  return (
    <div className="flex min-h-dvh">
      <AppSidebar
        onSelectRecent={selectRecent}
        onNewChat={startNewChat}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <main className="technical-grid relative flex min-h-dvh flex-1 flex-col overflow-y-auto">
        {/* Abrir menú en mobile */}
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          aria-label="Abrir menú"
          className="absolute left-4 top-4 z-10 flex h-11 w-11 items-center justify-center rounded-lg border border-line-subtle bg-sidebar text-text-secondary transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand md:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        <div className="flex flex-1 flex-col items-center justify-center px-4 pb-8 pt-20 md:px-6 md:pt-8">
          <div className="w-[calc(100%-16px)] max-w-[900px] md:w-[calc(100%-48px)] -mt-[6vh]">
            <h1 className="mb-8 text-center text-[28px] font-medium text-text-primary md:text-[34px]">
              ¿Qué necesitas revisar?
            </h1>

            <ChatComposer
              ref={composerRef}
              value={value}
              onChange={setValue}
              onSubmit={ask}
              loading={loading}
            />

            {(loading || result || error) && (
              <div
                className={cn(
                  "mt-6 rounded-2xl border border-line bg-surface p-5 text-[15px] leading-relaxed text-text-primary whitespace-pre-wrap",
                  loading && "text-text-secondary"
                )}
              >
                {loading && (
                  <BouncingDots
                    className="h-2 w-2 bg-text-subtle"
                    animate={{ y: [0, -8, 0] }}
                    message="Buscando en la normativa…"
                    messagePlacement="right"
                  />
                )}
                {error && `⚠️ ${error}`}
                {result && (
                  <>
                    {result.answer}
                    <div className="mt-4 text-[13px] text-text-secondary">
                      Fuentes:{" "}
                      {result.sources
                        .map((s) => `${s.source} (págs. ${s.pages.join(", ")})`)
                        .join(" · ")}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        <p className="px-4 pb-[max(1.25rem,env(safe-area-inset-bottom))] text-center text-[13px] text-text-secondary">
          Verifica siempre la normativa vigente y su aplicación a tu caso.
        </p>
      </main>
    </div>
  );
}
