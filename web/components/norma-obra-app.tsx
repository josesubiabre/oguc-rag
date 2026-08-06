"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Menu } from "lucide-react";

import { AppSidebar } from "@/components/app-sidebar";
import { ChatComposer, ChatComposerHandle } from "@/components/chat-composer";
import { LegalDisclaimerModal } from "@/components/legal-disclaimer";
import { BouncingDots } from "@/components/ui/bouncing-dots";
import {
  ChatMessage,
  useConversations,
} from "@/hooks/use-conversations";

export function NormaObraApp() {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [legalOpen, setLegalOpen] = useState(false);
  const composerRef = useRef<ChatComposerHandle>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const { conversations, upsert, get } = useConversations();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const ask = useCallback(async () => {
    const question = value.trim();
    if (!question || loading) return;

    const withQuestion: ChatMessage[] = [
      ...messages,
      { role: "user", content: question },
    ];
    setMessages(withQuestion);
    setValue("");
    composerRef.current?.resetHeight();
    setLoading(true);
    setError(null);

    let final = withQuestion;
    try {
      const r = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail ?? "Error inesperado");
      final = [
        ...withQuestion,
        { role: "assistant", content: data.answer, sources: data.sources },
      ];
      setMessages(final);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setLoading(false);
      composerRef.current?.focus();
    }

    // Persistir la conversación (crea una nueva si es la primera pregunta)
    const id = activeId ?? crypto.randomUUID();
    if (!activeId) setActiveId(id);
    upsert({
      id,
      title: final[0].content.slice(0, 60),
      messages: final,
      updatedAt: Date.now(),
    });
  }, [value, loading, messages, activeId, upsert]);

  const startNewChat = useCallback(() => {
    setMessages([]);
    setActiveId(null);
    setValue("");
    setError(null);
    setMobileOpen(false);
    composerRef.current?.resetHeight();
    composerRef.current?.focus();
  }, []);

  const selectConversation = useCallback(
    (id: string) => {
      const conversation = get(id);
      if (!conversation) return;
      setMessages(conversation.messages);
      setActiveId(id);
      setError(null);
      setMobileOpen(false);
      composerRef.current?.focus();
    },
    [get]
  );

  const hasThread = messages.length > 0;

  const composer = (
    <ChatComposer
      ref={composerRef}
      value={value}
      onChange={setValue}
      onSubmit={ask}
      loading={loading}
    />
  );

  return (
    <div className="flex h-dvh">
      <AppSidebar
        conversations={conversations}
        activeId={activeId}
        onSelectConversation={selectConversation}
        onNewChat={startNewChat}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <main className="technical-grid relative flex h-dvh flex-1 flex-col">
        {/* Abrir menú en mobile */}
        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          aria-label="Abrir menú"
          className="absolute left-4 top-4 z-10 flex h-11 w-11 items-center justify-center rounded-lg border border-line-subtle bg-sidebar text-text-secondary transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand md:hidden"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>

        {!hasThread ? (
          /* Pantalla inicial: bienvenida centrada */
          <div className="flex flex-1 flex-col items-center justify-center px-4 pb-8 pt-20 md:px-6 md:pt-8">
            <div className="w-[calc(100%-16px)] max-w-[900px] md:w-[calc(100%-48px)] -mt-[6vh]">
              <h1 className="mb-8 text-center text-[28px] font-medium text-text-primary md:text-[34px]">
                ¿Qué necesitas revisar?
              </h1>
              {composer}
              {error && (
                <div className="mt-6 rounded-2xl border border-line bg-surface p-5 text-[15px] text-text-primary">
                  ⚠️ {error}
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Conversación activa: hilo scrolleable + composer abajo */
          <>
            <div className="min-h-0 flex-1 overflow-y-auto px-4 pt-16 md:px-6 md:pt-8">
              <div className="mx-auto w-[calc(100%-16px)] max-w-[900px] space-y-4 pb-4 md:w-[calc(100%-48px)]">
                {messages.map((m, i) =>
                  m.role === "user" ? (
                    <div key={i} className="flex justify-end">
                      <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-surface-hover px-4 py-3 text-[15px] leading-relaxed text-text-primary">
                        {m.content}
                      </div>
                    </div>
                  ) : (
                    <div
                      key={i}
                      className="whitespace-pre-wrap rounded-2xl border border-line bg-surface p-5 text-[15px] leading-relaxed text-text-primary"
                    >
                      {m.content}
                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-4 text-[13px] text-text-secondary">
                          Fuentes:{" "}
                          {m.sources
                            .map(
                              (s) => `${s.source} (págs. ${s.pages.join(", ")})`
                            )
                            .join(" · ")}
                        </div>
                      )}
                    </div>
                  )
                )}

                {loading && (
                  <div className="rounded-2xl border border-line bg-surface p-5 text-text-secondary">
                    <BouncingDots
                      className="h-2 w-2 bg-text-subtle"
                      animate={{ y: [0, -8, 0] }}
                      message="Buscando en la normativa…"
                      messagePlacement="right"
                    />
                  </div>
                )}
                {error && (
                  <div className="rounded-2xl border border-line bg-surface p-5 text-[15px] text-text-primary">
                    ⚠️ {error}
                  </div>
                )}
                <div ref={endRef} />
              </div>
            </div>

            <div className="px-4 pb-2 md:px-6">
              <div className="mx-auto w-[calc(100%-16px)] max-w-[900px] md:w-[calc(100%-48px)]">
                {composer}
              </div>
            </div>
          </>
        )}

        <p className="shrink-0 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-2 text-center text-[13px] text-text-secondary">
          Verifica siempre la normativa vigente y su aplicación a tu caso.{" "}
          <button
            type="button"
            onClick={() => setLegalOpen(true)}
            className="underline underline-offset-2 transition-colors hover:text-text-primary focus-visible:outline-2 focus-visible:outline-brand"
          >
            Aviso legal
          </button>
        </p>

        <LegalDisclaimerModal
          open={legalOpen}
          onClose={() => setLegalOpen(false)}
        />
      </main>
    </div>
  );
}
