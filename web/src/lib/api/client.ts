import { apiBaseUrl } from "@/lib/config";
import type {
  ChatSession,
  MeResponse,
  RequestTrace,
  ResearchResponse,
  SessionMessage,
} from "@/lib/types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  accessToken: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

export async function listSessions(accessToken: string): Promise<ChatSession[]> {
  const data = await request<{ sessions: ChatSession[] }>(
    "/sessions",
    accessToken,
  );
  return data.sessions;
}

export async function createSession(accessToken: string): Promise<ChatSession> {
  const data = await request<{ session: ChatSession }>("/sessions", accessToken, {
    method: "POST",
  });
  return data.session;
}

export async function deleteSession(
  accessToken: string,
  sessionId: string,
): Promise<void> {
  await request<void>(`/sessions/${sessionId}`, accessToken, {
    method: "DELETE",
  });
}

export async function listSessionMessages(
  accessToken: string,
  sessionId: string,
): Promise<SessionMessage[]> {
  const data = await request<{ messages: SessionMessage[] }>(
    `/sessions/${sessionId}/messages`,
    accessToken,
  );
  return data.messages;
}

export async function postSessionMessage(
  accessToken: string,
  sessionId: string,
  query: string,
): Promise<{ message: SessionMessage; research: ResearchResponse }> {
  return request(`/sessions/${sessionId}/messages`, accessToken, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function fetchMe(accessToken: string): Promise<MeResponse> {
  return request<MeResponse>("/me", accessToken);
}

export async function fetchRequestTrace(
  accessToken: string,
  traceId: string,
): Promise<RequestTrace> {
  return request<RequestTrace>(`/traces/${traceId}`, accessToken);
}

export function formatQueryMode(mode: string): string {
  return mode.replaceAll("_", " ");
}
