"use client";

import { useCallback, useSyncExternalStore } from "react";

export interface Source {
  source: string;
  pages: number[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: number;
}

const STORAGE_KEY = "normaobra:conversations";
const MAX_CONVERSATIONS = 50;
const EMPTY: Conversation[] = [];

/* Almacén externo mínimo sobre localStorage, compatible con SSR. */
let cache: Conversation[] | null = null;
const listeners = new Set<() => void>();

function read(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Conversation[]) : EMPTY;
  } catch {
    return EMPTY;
  }
}

function getSnapshot(): Conversation[] {
  if (cache === null) cache = read();
  return cache;
}

function getServerSnapshot(): Conversation[] {
  return EMPTY;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function write(next: Conversation[]) {
  cache = next;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // almacenamiento lleno o bloqueado: la sesión sigue funcionando en memoria
  }
  listeners.forEach((l) => l());
}

/** Historial de conversaciones persistido en localStorage (por navegador). */
export function useConversations() {
  const conversations = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );

  const upsert = useCallback((conversation: Conversation) => {
    const rest = getSnapshot().filter((c) => c.id !== conversation.id);
    write([conversation, ...rest].slice(0, MAX_CONVERSATIONS));
  }, []);

  const get = useCallback(
    (id: string) => conversations.find((c) => c.id === id) ?? null,
    [conversations]
  );

  return { conversations, upsert, get };
}
