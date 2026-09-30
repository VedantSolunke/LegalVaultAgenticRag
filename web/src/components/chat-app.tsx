"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { ResearchMessage } from "@/components/research-message";
import { DisclaimerBanner } from "@/components/disclaimer-banner";
import {
  createSession,
  deleteSession,
  listSessionMessages,
  listSessions,
  postSessionMessage,
} from "@/lib/api/client";
import { displaySessionTitle } from "@/lib/session-title";
import type { ChatSession, SessionMessage } from "@/lib/types";

export function ChatApp() {
  const router = useRouter();
  const { accessToken, isAdmin, ready, signOut } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<SessionMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [sessionPendingDelete, setSessionPendingDelete] = useState<ChatSession | null>(
    null,
  );
  const [deletingSession, setDeletingSession] = useState(false);

  useEffect(() => {
    if (!ready) {
      return;
    }
    if (!accessToken) {
      router.replace("/login");
    }
  }, [ready, accessToken, router]);

  const loadSessions = useCallback(async () => {
    if (!accessToken) {
      setSessions([]);
      setActiveSessionId(null);
      setMessages([]);
      return;
    }
    setLoadingSessions(true);
    setError(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    try {
      const next = await listSessions(accessToken);
      setSessions(next);
      setActiveSessionId(next[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setLoadingSessions(false);
    }
  }, [accessToken]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!accessToken || !activeSessionId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    setLoadingMessages(true);
    setError(null);
    listSessionMessages(accessToken, activeSessionId)
      .then((rows) => {
        if (!cancelled) {
          setMessages(rows);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load messages");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingMessages(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, activeSessionId]);

  function requestDeleteSession(session: ChatSession) {
    setSessionPendingDelete(session);
  }

  function cancelDeleteSession() {
    if (deletingSession) {
      return;
    }
    setSessionPendingDelete(null);
  }

  async function confirmDeleteSession() {
    const session = sessionPendingDelete;
    if (!accessToken || !session || deletingSession) {
      return;
    }
    setDeletingSession(true);
    setError(null);
    try {
      await deleteSession(accessToken, session.id);
      setSessions((prev) => {
        const next = prev.filter((s) => s.id !== session.id);
        if (activeSessionId === session.id) {
          setActiveSessionId(next[0]?.id ?? null);
          setMessages([]);
        }
        return next;
      });
      setSessionPendingDelete(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete session");
    } finally {
      setDeletingSession(false);
    }
  }

  async function onNewSession() {
    if (!accessToken) {
      return;
    }
    setError(null);
    try {
      const session = await createSession(accessToken);
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    }
  }

  async function onSend(event: FormEvent) {
    event.preventDefault();
    const query = draft.trim();
    if (!accessToken || !activeSessionId || !query || sending) {
      return;
    }
    setSending(true);
    setError(null);
    setDraft("");
    try {
      await postSessionMessage(accessToken, activeSessionId, query);
      const refreshed = await listSessionMessages(accessToken, activeSessionId);
      setMessages(refreshed);
      await loadSessions();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      setDraft(query);
    } finally {
      setSending(false);
    }
  }

  function handleSignOut() {
    signOut();
    router.replace("/login");
  }

  if (!ready || !accessToken) {
    return null;
  }

  const pendingDeleteTitle = sessionPendingDelete
    ? displaySessionTitle(sessionPendingDelete.title)
    : "";

  return (
    <div className="flex h-dvh flex-col overflow-hidden bg-slate-50">
      {sessionPendingDelete && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
          role="presentation"
          onClick={cancelDeleteSession}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-session-title"
            aria-describedby="delete-session-description"
            className="w-full max-w-sm rounded-lg border border-slate-200 bg-white p-5 shadow-lg"
            onClick={(event) => event.stopPropagation()}
          >
            <h3
              id="delete-session-title"
              className="text-base font-semibold text-slate-900"
            >
              Delete chat?
            </h3>
            <p id="delete-session-description" className="mt-2 text-sm text-slate-600">
              This will permanently delete{" "}
              <span className="font-medium text-slate-800">{pendingDeleteTitle}</span> and
              its messages. This cannot be undone.
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={cancelDeleteSession}
                disabled={deletingSession}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmDeleteSession}
                disabled={deletingSession}
                className="rounded-md bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deletingSession ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
      <header className="border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">LegalVault Research</h1>
            <p className="text-xs text-slate-500">BNS legal research assistant</p>
          </div>
          <button
            type="button"
            onClick={handleSignOut}
            className="text-sm text-slate-600 hover:text-slate-900"
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 gap-0 md:gap-4 md:p-4">
        <aside className="flex min-h-0 w-full max-w-xs shrink-0 flex-col border-r border-slate-200 bg-white md:rounded-lg md:border">
          <div className="flex items-center justify-between border-b border-slate-100 p-3">
            <h2 className="text-sm font-semibold text-slate-800">Sessions</h2>
            <button
              type="button"
              onClick={onNewSession}
              className="rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-white hover:bg-slate-800"
            >
              New
            </button>
          </div>
          <ul className="min-h-0 flex-1 overflow-y-auto p-2">
            {loadingSessions && sessions.length === 0 && (
              <li className="px-2 py-3 text-sm text-slate-500">Loading…</li>
            )}
            {sessions.map((session) => (
              <li key={session.id} className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setActiveSessionId(session.id)}
                  title={session.title ?? undefined}
                  className={`min-w-0 flex-1 rounded-md px-2 py-2 text-left text-sm ${
                    session.id === activeSessionId
                      ? "bg-slate-100 font-medium text-slate-900"
                      : "text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  <span className="block truncate">
                    {displaySessionTitle(session.title)}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => requestDeleteSession(session)}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 shadow-sm hover:border-red-200 hover:bg-red-50 hover:text-red-700"
                  aria-label={`Delete ${displaySessionTitle(session.title)}`}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-4 w-4"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.52.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="flex min-h-0 flex-1 flex-col bg-white md:rounded-lg md:border md:border-slate-200">
          <div className="border-b border-slate-100 p-3">
            <DisclaimerBanner />
          </div>

          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
            {!activeSessionId && (
              <p className="text-sm text-slate-600">
                Create a session to start researching BNS provisions.
              </p>
            )}
            {loadingMessages && <p className="text-sm text-slate-500">Loading messages…</p>}
            {messages.map((message) => (
              <article
                key={message.id}
                className={`rounded-lg p-3 ${
                  message.role === "user"
                    ? "ml-8 bg-slate-100 text-slate-900"
                    : "mr-8 border border-slate-200 bg-white"
                }`}
              >
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap text-sm">{message.body}</p>
                ) : message.research ? (
                  <ResearchMessage
                    research={message.research}
                    accessToken={accessToken}
                    isAdmin={isAdmin}
                  />
                ) : (
                  <p className="whitespace-pre-wrap text-sm text-slate-800">{message.body}</p>
                )}
              </article>
            ))}
          </div>

          {error && (
            <p className="px-4 text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <form
            onSubmit={onSend}
            className="flex gap-2 border-t border-slate-100 p-3"
          >
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about a BNS section or describe a fact pattern…"
              rows={2}
              disabled={!activeSessionId || sending}
              className="min-h-[3rem] flex-1 resize-y rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm leading-relaxed text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
            />
            <button
              type="submit"
              disabled={!activeSessionId || sending || !draft.trim()}
              className="self-end rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              {sending ? "Sending…" : "Send"}
            </button>
          </form>
        </main>
      </div>
    </div>
  );
}
