import { apiFetch } from "./client";
import type { ChatHistoryResponse } from "./types";

export function getChatHistory(params: { beforeSequence?: number; limit?: number } = {}) {
  const query = new URLSearchParams();
  if (params.beforeSequence) query.set("before_sequence", String(params.beforeSequence));
  query.set("limit", String(params.limit ?? 50));
  return apiFetch<ChatHistoryResponse>(`/api/v1/chat/messages?${query.toString()}`);
}

export function reportMessage(messageId: string, reason: string) {
  return apiFetch<void>(`/api/v1/chat/messages/${messageId}/report`, { method: "POST", body: { reason } });
}

export function hideMessage(messageId: string, reason: string) {
  return apiFetch<void>(`/api/v1/chat/messages/${messageId}/hide`, { method: "POST", body: { reason } });
}

/** Same-origin so it works through both the gateway and the Vite dev proxy. */
export function chatWebSocketUrl(): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/ws/chat`;
}
