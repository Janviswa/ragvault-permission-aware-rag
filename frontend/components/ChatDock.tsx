"use client";

import { createContext, FormEvent, KeyboardEvent, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, apiRequest, streamRequest } from "@/lib/api";
import { useSession } from "@/lib/session";
import { chatBucket, formatDateTime } from "@/lib/format";
import type { ChatDetail, ChatMessage, ChatSummary, RestrictedDocument, Source } from "@/lib/types";
import { IconChat, IconDocument, IconHistory, IconMaximize, IconMinus, IconNewChat, IconSend, IconStop, IconTrash, IconX } from "./Icons";
import { Markdown } from "./Markdown";
import { Tip } from "./Tip";

type View = "chat" | "history";

// Must match the marker the server saves when an answer is cut short.
const STOPPED_MARK = "\n\n*— stopped —*";

type ChatApi = {
  /** Open the assistant, optionally loading a saved conversation. */
  openChat: (chatId?: number) => void;
  /** Bumps whenever a conversation is created, changed or deleted, so lists can refresh. */
  version: number;
  // internals used by <ChatWindow> and <ChatBubble>
  open: boolean;
  setOpen: (open: boolean) => void;
  /** Collapse the window back to the bubble (keeps the conversation). */
  minimize: () => void;
  view: View;
  setView: (view: View) => void;
  maximized: boolean;
  setMaximized: (value: boolean) => void;
  chatId: number | null;
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  sending: boolean;
  loadingChat: boolean;
  error: string;
  send: () => Promise<void>;
  /** Stop the answer that is being written. What was written so far is kept. */
  stop: () => void;
  reset: () => void;
  deleteChat: (id: number) => Promise<void>;
};

const ChatContext = createContext<ChatApi | null>(null);

export function useChat(): ChatApi {
  const value = useContext(ChatContext);
  if (!value) throw new Error("useChat must be used inside <ChatProvider>");
  return value;
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const { handleError } = useSession();
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<View>("chat");
  const [maximized, setMaximized] = useState(false);
  const [chatId, setChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  const minimize = useCallback(() => {
    setMaximized(false);
    setOpen(false);
  }, []);

  const reset = useCallback(() => {
    setChatId(null);
    setMessages([]);
    setInput("");
    setError("");
    setView("chat");
  }, []);

  const openChat = useCallback(
    async (id?: number) => {
      setOpen(true);
      setView("chat");
      if (id === undefined) return;
      setLoadingChat(true);
      setError("");
      try {
        const chat = await apiRequest<ChatDetail>(`/chats/${id}`);
        setChatId(chat.id);
        setMessages(chat.messages);
      } catch (cause) {
        setError(handleError(cause));
      } finally {
        setLoadingChat(false);
      }
    },
    [handleError],
  );

  const abortRef = useRef<AbortController | null>(null);
  const pendingRef = useRef(""); // pieces received but not painted yet
  const frameRef = useRef<number | null>(null);

  const stop = useCallback(() => abortRef.current?.abort(), []);

  const send = useCallback(async () => {
    const question = input.trim();
    if (!question || sending) return;

    const stamp = Date.now();
    const userId = `local-${stamp}`;
    const answerId = `stream-${stamp}`;
    setMessages((current) => [...current, { id: userId, role: "user", content: question, sources: [], restricted: null }]);
    setInput("");
    setSending(true);
    setError("");

    const controller = new AbortController();
    abortRef.current = controller;
    let gotMeta = false;
    let finished = false;
    let received = "";

    // Paint at most once per frame, however many pieces arrive.
    const flush = () => {
      frameRef.current = null;
      const chunk = pendingRef.current;
      if (!chunk) return;
      pendingRef.current = "";
      setMessages((current) => current.map((m) => (m.id === answerId ? { ...m, content: m.content + chunk } : m)));
    };
    const cancelFrame = () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      pendingRef.current = "";
    };
    const markInterrupted = () => {
      cancelFrame();
      const text = received ? received + STOPPED_MARK : STOPPED_MARK.trim();
      setMessages((current) => current.map((m) => (m.id === answerId ? { ...m, content: text, streaming: false } : m)));
      setVersion((v) => v + 1);
    };

    try {
      await streamRequest("/rag/query/stream", {
        body: { question, limit: 5, chat_id: chatId },
        signal: controller.signal,
        onEvent: (event, data) => {
          if (event === "meta") {
            gotMeta = true;
            setChatId(data.chat_id);
            setMessages((current) => [
              ...current,
              { id: answerId, role: "assistant", content: "", sources: data.sources, restricted: data.restricted, streaming: !data.restricted },
            ]);
            setVersion((v) => v + 1);
          } else if (event === "token") {
            received += data.t;
            pendingRef.current += data.t;
            if (frameRef.current === null) frameRef.current = requestAnimationFrame(flush);
          } else if (event === "done") {
            finished = true;
            cancelFrame();
            setMessages((current) => current.map((m) => (m.id === answerId ? { ...m, content: data.answer, streaming: false } : m)));
            setVersion((v) => v + 1);
          } else if (event === "error") {
            finished = true;
            markInterrupted();
            setError(data.message);
          }
        },
      });
      if (!finished && gotMeta) markInterrupted(); // connection ended without a final event
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        if (gotMeta) markInterrupted(); // the person pressed Stop: keep what was written
        else {
          setMessages((current) => current.filter((m) => m.id !== userId));
          setInput(question);
        }
      } else if (gotMeta) {
        markInterrupted();
        setError(handleError(cause));
      } else {
        // Failed before anything came back: take the question out of the transcript and put it back in the box.
        setMessages((current) => current.filter((m) => m.id !== userId));
        setInput(question);
        if (cause instanceof ApiError && cause.status === 404 && chatId !== null) {
          setChatId(null);
          setError("That conversation no longer exists. Your question will start a new chat.");
        } else {
          setError(handleError(cause));
        }
      }
    } finally {
      cancelFrame();
      abortRef.current = null;
      setSending(false);
    }
  }, [input, sending, chatId, handleError]);

  const deleteChat = useCallback(
    async (id: number) => {
      await apiRequest(`/chats/${id}`, { method: "DELETE" });
      if (id === chatId) {
        setChatId(null);
        setMessages([]);
      }
      setVersion((v) => v + 1);
    },
    [chatId],
  );

  const api = useMemo<ChatApi>(
    () => ({
      openChat, version, open, setOpen, minimize, view, setView, maximized, setMaximized, chatId, messages, input, setInput,
      sending, loadingChat, error, send, stop, reset, deleteChat,
    }),
    [openChat, version, open, minimize, view, maximized, chatId, messages, input, sending, loadingChat, error, send, stop, reset, deleteChat],
  );

  return <ChatContext.Provider value={api}>{children}</ChatContext.Provider>;
}

/* -------------------------------------------------------------------------- */

export function ChatBubble() {
  const { open, openChat } = useChat();
  // Always mounted so it can shrink away as the window grows from its corner, and pop back on close.
  return (
    <button
      onClick={() => openChat()}
      aria-label="Open assistant"
      aria-hidden={open}
      tabIndex={open ? -1 : 0}
      className={`absolute bottom-4 right-3 z-20 flex h-14 w-14 origin-center items-center justify-center rounded-full border border-white/80 bg-gradient-to-br from-[#5468d8] to-[#7660d4] text-onaccent shadow-soft transition-all duration-300 ease-out hover:brightness-90 md:right-2 dark:border-[rgb(255_255_255/0.15)] ${
        open ? "pointer-events-none scale-0 rotate-90 opacity-0" : "scale-100 rotate-0 opacity-100"
      }`}
    >
      {!open && <span aria-hidden="true" className="absolute inset-0 -z-10 animate-ping-soft rounded-full bg-periwinkle" />}
      <IconChat size={24} />
    </button>
  );
}

function Dot({ color, border, label, onClick, children }: { color: string; border: string; label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      title={label}
      className="flex h-[14px] w-[14px] items-center justify-center rounded-full border text-black/60"
      style={{ background: color, borderColor: border }}
    >
      <span className="opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">{children}</span>
    </button>
  );
}

export function ChatWindow() {
  const chat = useChat();
  const { me } = useSession();
  const scrollRef = useRef<HTMLDivElement>(null);
  const stickRef = useRef(true); // follow new text only while the reader is at the bottom
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { open, view, messages, sending, loadingChat } = chat;

  // Keep the window mounted while its close animation plays.
  const [mounted, setMounted] = useState(open);
  const [closing, setClosing] = useState(false);
  useEffect(() => {
    if (open) {
      setMounted(true);
      setClosing(false);
    } else if (mounted) {
      setClosing(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || !open || view !== "chat") return;
    if (messages[messages.length - 1]?.role === "user") stickRef.current = true;
    if (stickRef.current) el.scrollTop = el.scrollHeight;
  }, [messages, sending, open, view]);

  useEffect(() => {
    if (open && view === "chat" && !loadingChat) inputRef.current?.focus();
  }, [open, view, loadingChat, chat.chatId]);

  if (!mounted) return null;

  const inHistory = view === "history";

  function back() {
    if (inHistory) chat.setView("chat");
    else chat.minimize();
  }

  function onKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === "Escape") back();
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    chat.send();
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      chat.send();
    }
  }

  return (
    <section
      aria-label="Assistant"
      onKeyDown={onKeyDown}
      onAnimationEnd={(event) => {
        if (closing && event.target === event.currentTarget) {
          setMounted(false);
          setClosing(false);
        }
      }}
      className={`${chat.maximized ? "fixed inset-2 z-50" : "absolute inset-0 z-30"} flex origin-bottom-right flex-col overflow-hidden rounded-[22px] border border-line bg-canvas shadow-soft ${
        closing ? "pointer-events-none animate-chat-out" : "animate-chat-in"
      }`}
    >
      {/* one bar: window dots, Back, title, History, New chat */}
      <div className="relative flex h-12 shrink-0 items-center justify-between gap-2 border-b border-line bg-white/80 px-3 sm:px-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="group flex items-center gap-2">
            <Dot color="#ff5f57" border="#e0443e" label="Close and end this chat" onClick={() => { chat.minimize(); chat.reset(); }}>
              <IconX size={8} strokeWidth={3} />
            </Dot>
            <Dot color="#febc2e" border="#d99e1c" label="Minimize assistant" onClick={chat.minimize}>
              <IconMinus size={8} strokeWidth={3} />
            </Dot>
            <Dot color="#28c840" border="#1fa433" label={chat.maximized ? "Exit full screen" : "Full screen"} onClick={() => chat.setMaximized(!chat.maximized)}>
              <IconMaximize size={8} strokeWidth={3} />
            </Dot>
          </div>
        </div>

        <h2 className="pointer-events-none absolute inset-x-0 hidden text-center font-mono text-[12px] text-ash lg:block">ragvault.ai — assistant</h2>

        <div className="relative flex shrink-0 items-center gap-1.5">
          <Tip label={inHistory ? "Back to chat" : "History"}>
            <button
              onClick={() => chat.setView(inHistory ? "chat" : "history")}
              aria-pressed={inHistory}
              aria-label={inHistory ? "Back to chat" : "History"}
              className={`${inHistory ? "btn-solid" : "btn-line"} h-9 w-9 !p-0`}
            >
              <IconHistory size={17} />
            </button>
          </Tip>
          <Tip label="New chat" align="end">
            <button onClick={chat.reset} aria-label="New chat" className="btn-line h-9 w-9 !p-0">
              <IconNewChat size={17} />
            </button>
          </Tip>
        </div>
      </div>

      {inHistory ? (
        <HistoryList />
      ) : (
        <>
          <div
            ref={scrollRef}
            onScroll={(e) => {
              const el = e.currentTarget;
              stickRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
            }}
            className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-8"
            role="log"
            aria-live="off"
            aria-label="Conversation"
          >
            <div className="space-y-7 font-mono text-[13px] leading-6">
              {loadingChat && <p className="text-ash">loading conversation…</p>}
              {!loadingChat && messages.length === 0 && !sending && (
                <div className="space-y-1">
                  <p className="text-ash">ragvault · signed in as {me.full_name} ({me.role})</p>
                  <p>Answers come only from documents you are allowed to open. Sources are listed with each answer.</p>
                  <p className="text-ash">Type a question below and press Enter.</p>
                </div>
              )}
              {messages.map((message) => (
                <Message key={message.id} message={message} name={me.full_name} role={me.role} />
              ))}
              {sending && messages[messages.length - 1]?.role === "user" && <p className="text-ash" role="status">searching the documents you may open…</p>}
              {chat.error && <p role="alert" className="note note-error !mb-0">error: {chat.error}</p>}
            </div>
          </div>

          <form onSubmit={onSubmit} className="shrink-0 border-t border-line bg-white/70 px-3 py-3 sm:px-8">
            <div className="flex items-end gap-3">
              <span className="pb-2.5 font-mono text-[14px] font-medium text-[#12803e] dark:text-[#5fe39a]" aria-hidden="true">$</span>
              <label htmlFor="chat-input" className="sr-only">Your question</label>
              <textarea
                id="chat-input"
                ref={inputRef}
                rows={1}
                value={chat.input}
                maxLength={4000}
                onChange={(event) => {
                  chat.setInput(event.target.value);
                  event.target.style.height = "auto";
                  event.target.style.height = `${Math.min(event.target.scrollHeight, 120)}px`;
                }}
                onKeyDown={onInputKeyDown}
                placeholder="ask a question…"
                disabled={loadingChat}
                className="field max-h-[120px] min-h-[42px] flex-1 resize-none font-mono text-[13px]"
              />
              {sending ? (
                <Tip label="Stop generating" side="top" align="end">
                  <button type="button" onClick={chat.stop} className="btn-solid h-[42px] w-[42px] shrink-0 !p-0" aria-label="Stop generating">
                    <IconStop size={18} />
                  </button>
                </Tip>
              ) : (
                <Tip label="Send" side="top" align="end">
                  <button type="submit" disabled={loadingChat || !chat.input.trim()} className="btn-solid h-[42px] w-[42px] shrink-0 !p-0" aria-label="Send question">
                    <IconSend size={17} />
                  </button>
                </Tip>
              )}
            </div>
          </form>
        </>
      )}
    </section>
  );
}

/* -------------------------------------------------------------------------- */

function HistoryList() {
  const chat = useChat();
  const { handleError } = useSession();
  const [items, setItems] = useState<ChatSummary[] | null>(null);
  const [error, setError] = useState("");
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const { version } = chat;

  useEffect(() => {
    let cancelled = false;
    apiRequest<ChatSummary[]>("/chats")
      .then((rows) => !cancelled && (setItems(rows), setError("")))
      .catch((cause) => !cancelled && setError(handleError(cause)));
    return () => {
      cancelled = true;
    };
  }, [version, handleError]);

  const groups = useMemo(() => {
    const buckets: Record<string, ChatSummary[]> = { Today: [], "This week": [], Earlier: [] };
    for (const item of items ?? []) buckets[chatBucket(item.updated_at)].push(item);
    return (["Today", "This week", "Earlier"] as const).map((label) => ({ label, items: buckets[label] })).filter((g) => g.items.length);
  }, [items]);

  async function remove(id: number) {
    setBusy(true);
    try {
      await chat.deleteChat(id);
      setConfirmId(null);
    } catch (cause) {
      setError(handleError(cause));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-8" aria-label="Chat history">
      <div className="font-mono text-[13px] leading-6">
        <p className="mb-4 text-ash">$ history — your past conversations (only you can see them)</p>
        {error && <p role="alert" className="note note-error">error: {error}</p>}
        {items === null && !error && <p className="text-ash">loading…</p>}
        {items !== null && groups.length === 0 && (
          <p>No chats yet. <button className="font-semibold text-accent underline underline-offset-4" onClick={() => chat.setView("chat")}>Ask your first question</button>.</p>
        )}
        <div className="space-y-6">
          {groups.map((group) => (
            <section key={group.label} aria-label={group.label}>
              <h3 className="mb-2 text-[12px] font-semibold uppercase tracking-wider text-ash">{group.label}</h3>
              <ul className="space-y-2">
                {group.items.map((item) => (
                  <li key={item.id} className={`flex items-center gap-2 rounded-xl border bg-white/80 pr-2 ${item.id === chat.chatId ? "border-periwinkle-deep" : "border-line"}`}>
                    <button onClick={() => chat.openChat(item.id)} className="min-w-0 flex-1 rounded-xl px-4 py-3 text-left hover:bg-white">
                      <span className="block truncate font-medium">{item.title}</span>
                      <span className="block text-[12px] text-ash">{formatDateTime(item.updated_at)} · {Math.ceil(item.message_count / 2)} {Math.ceil(item.message_count / 2) === 1 ? "question" : "questions"}</span>
                    </button>
                    {confirmId === item.id ? (
                      <span className="flex shrink-0 items-center gap-1.5" role="group" aria-label={`Confirm deleting ${item.title}`}>
                        <button className="btn-solid btn-sm" disabled={busy} onClick={() => remove(item.id)}>Delete</button>
                        <button className="btn-quiet btn-sm" onClick={() => setConfirmId(null)}>Cancel</button>
                      </span>
                    ) : (
                      <button className="btn-quiet btn-sm shrink-0" onClick={() => setConfirmId(item.id)} aria-label={`Delete chat ${item.title}`}>
                        <IconTrash size={15} />
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */

function groupSources(sources: Source[]) {
  const byDocument = new Map<number, { title: string; file_name: string; passages: number[] }>();
  for (const source of sources) {
    const entry = byDocument.get(source.document_id) ?? { title: source.title, file_name: source.file_name, passages: [] };
    entry.passages.push(source.chunk_index + 1);
    byDocument.set(source.document_id, entry);
  }
  return Array.from(byDocument.entries()).map(([id, value]) => ({ id, ...value, passages: Array.from(new Set(value.passages)).sort((a, b) => a - b) }));
}

function SectionLabel({ icon, children }: { icon?: ReactNode; children: ReactNode }) {
  return (
    <p className="flex items-center gap-2 font-sans text-[11.5px] font-bold uppercase tracking-[0.08em] text-ash">
      {icon}
      {children}
    </p>
  );
}

function Message({ message, name, role }: { message: ChatMessage; name: string; role: string }) {
  if (message.role === "user") {
    // 1) what you asked
    return (
      <div className="rounded-2xl border border-periwinkle/35 bg-periwinkle/10 px-4 py-3">
        <p className="break-words">
          <span className="select-none font-medium text-[#12803e] dark:text-[#5fe39a]">$ </span>
          <span className="whitespace-pre-wrap font-medium">{message.content}</span>
        </p>
        <p className="pl-4 text-ash">asking as {name}, role: {role}</p>
      </div>
    );
  }

  if (message.restricted) return <RestrictedBlock info={message.restricted} text={message.content} />;

  const sources = groupSources(message.sources);
  return (
    <div className="space-y-3">
      {/* 2) what was retrieved (system output) */}
      {sources.length > 0 && (
        <section aria-label="Retrieved sources" className="rounded-2xl border border-sky/50 bg-sky/10 px-4 py-3 dark:border-sky/25 dark:bg-sky/5">
          <SectionLabel icon={<IconDocument size={14} />}>Retrieved · only what you may open</SectionLabel>
          <div className="mt-2 overflow-x-auto">
            <div className="grid min-w-[420px] grid-cols-[minmax(0,1.2fr)_minmax(0,1.2fr)_auto] gap-x-6 text-ash">
              <span>doc</span><span>title</span><span>passages</span>
            </div>
            <div className="mt-1 border-t border-line pt-1">
              {sources.map((source) => (
                <div key={source.id} className="grid min-w-[420px] grid-cols-[minmax(0,1.2fr)_minmax(0,1.2fr)_auto] gap-x-6">
                  <span className="truncate font-medium text-[#2a50d0] dark:text-[#9db4ff]">{source.file_name}</span>
                  <span className="truncate">{source.title}</span>
                  <span>{source.passages.join(", ")}</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* 3) the generated answer */}
      <article aria-label="Answer" className="rounded-2xl border border-line bg-white shadow-lift">
        <header className="flex items-center gap-2 border-b border-fog px-4 py-2">
          <span aria-hidden="true" className="inline-block h-2.5 w-2.5 rounded-full bg-gradient-to-br from-[#5468d8] to-[#7660d4]" />
          <SectionLabel>RAGVault answer</SectionLabel>
        </header>
        <div className="px-4 py-3 font-sans text-[14px] leading-relaxed" aria-busy={message.streaming || undefined}>
          {message.content ? <Markdown text={message.content} /> : message.streaming ? <p className="text-ash">writing…</p> : null}
          {message.streaming && <span aria-hidden="true" className="mt-1 inline-block h-[15px] w-[7px] animate-pulse rounded-[2px] bg-accent align-middle" />}
        </div>
      </article>
    </div>
  );
}

type RequestState = "idle" | "form" | "sending" | "sent" | "already" | "error";

function RestrictedBlock({ info, text }: { info: RestrictedDocument; text: string }) {
  const { handleError } = useSession();
  const [state, setState] = useState<RequestState>("idle");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setState("sending");
    setMessage("");
    try {
      await apiRequest(`/documents/${info.document_id}/access-request`, {
        method: "POST",
        body: JSON.stringify({ reason: reason.trim().slice(0, 500) || null }),
      });
      setState("sent");
    } catch (cause) {
      if (cause instanceof ApiError && cause.status === 409) setState("already");
      else {
        setMessage(handleError(cause));
        setState("error");
      }
    }
  }

  return (
    <div>
      <div className="rounded-2xl border border-[#f0d28a] bg-[#fff7e1] p-4 text-[#5c3b00] dark:border-[#6b5420] dark:bg-[#33290f] dark:text-[#f6dc9a]">
        <p className="flex items-center gap-2 font-sans font-bold text-[#8a5300] dark:text-[#ffd27a]">
          <span aria-hidden="true">🔒</span> Access Restricted
        </p>
        <p className="mt-1.5 break-words">{text}</p>

        <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-0.5 border-t border-[#f0d28a] pt-3 dark:border-[#6b5420]">
          <dt className="text-[#8a6a2f] dark:text-[#c9ad66]">Document:</dt>
          <dd className="min-w-0 break-words font-medium">{info.file_name}</dd>
          <dt className="text-[#8a6a2f] dark:text-[#c9ad66]">Required role:</dt>
          <dd className="font-medium">{info.required_roles.join(" or ")}</dd>
          <dt className="text-[#8a6a2f] dark:text-[#c9ad66]">Your role:</dt>
          <dd className="font-medium">{info.your_role}</dd>
        </dl>

        <div className="mt-4">
          {state === "idle" && (
            <button onClick={() => setState("form")} className="btn-solid btn-sm">[Request Access]</button>
          )}
          {(state === "form" || state === "sending" || state === "error") && (
            <form onSubmit={submit} className="space-y-2.5">
              <label htmlFor={`reason-${info.document_id}`} className="block">
                Why do you need it? <span className="text-[#8a6a2f] dark:text-[#c9ad66]">(optional — the approver will see this)</span>
              </label>
              <textarea
                id={`reason-${info.document_id}`}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                maxLength={500}
                rows={2}
                disabled={state === "sending"}
                className="field resize-none font-mono text-[13px]"
                placeholder="e.g. Preparing next quarter's budget"
              />
              {state === "error" && <p role="alert" className="font-medium text-[#8a1c2f] dark:text-[#ffb3c1]">{message}</p>}
              <div className="flex gap-2">
                <button type="submit" disabled={state === "sending"} className="btn-solid btn-sm">{state === "sending" ? "Sending…" : "Send request"}</button>
                <button type="button" onClick={() => setState("idle")} disabled={state === "sending"} className="btn-quiet btn-sm">Cancel</button>
              </div>
            </form>
          )}
          {state === "sent" && <p role="status" className="font-semibold text-[#11613a] dark:text-[#9be8bf]">Request sent. You can follow it under Requests.</p>}
          {state === "already" && <p role="status" className="font-semibold">You already have a pending request for this document.</p>}
        </div>
      </div>
    </div>
  );
}
