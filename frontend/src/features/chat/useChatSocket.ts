import { useEffect, useRef, useState } from "react";
import * as chatApi from "@/lib/api/chat";
import type { ChatMessageResponse } from "@/lib/api/types";

type ConnectionStatus = "connecting" | "open" | "closed";

interface ChatEnvelope {
  type: string;
  client_message_id?: string;
  data?: Record<string, unknown>;
  message?: string;
}

export function useChatSocket(enabled: boolean) {
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [sendError, setSendError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;

    chatApi.getChatHistory({ limit: 50 }).then((history) => {
      if (!cancelled) setMessages(history.messages);
    });

    const ws = new WebSocket(chatApi.chatWebSocketUrl());
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => setStatus("open");
    ws.onclose = () => setStatus("closed");
    ws.onerror = () => setStatus("closed");
    ws.onmessage = (event) => {
      const envelope: ChatEnvelope = JSON.parse(event.data);

      if (envelope.type === "chat.ack" || envelope.type === "chat.message.created.v1") {
        const incoming = envelope.data as unknown as ChatMessageResponse;
        setMessages((current) => {
          if (current.some((message) => message.id === incoming.id)) return current;
          return [...current, incoming].sort((a, b) => a.sequence - b.sequence);
        });
      } else if (envelope.type === "chat.message.hidden.v1") {
        const { id } = envelope.data as { id: string };
        setMessages((current) =>
          current.map((message) =>
            message.id === id ? { ...message, hidden: true, text: "[message removed by a moderator]" } : message,
          ),
        );
      } else if (envelope.type === "error") {
        setSendError(envelope.message ?? "The message could not be sent.");
      }
    };

    return () => {
      cancelled = true;
      ws.close();
    };
  }, [enabled]);

  const send = (text: string) => {
    setSendError(null);
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      setSendError("Not connected yet. Please wait a moment and try again.");
      return;
    }
    const clientMessageId = crypto.randomUUID();
    wsRef.current.send(JSON.stringify({ type: "chat.send", client_message_id: clientMessageId, text }));
  };

  return { messages, status, send, sendError };
}
