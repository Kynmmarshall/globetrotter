import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Send, Flag, Wifi, WifiOff } from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/features/auth/AuthContext";
import { useChatSocket } from "@/features/chat/useChatSocket";
import * as chatApi from "@/lib/api/chat";
import { Spinner } from "@/components/ui/Spinner";
import { Button } from "@/components/ui/Button";

export function ChatPage() {
  const { user } = useAuth();
  const { messages, status, send, sendError } = useChatSocket(Boolean(user));
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const reportMutation = useMutation({
    mutationFn: (messageId: string) => chatApi.reportMessage(messageId, "Reported from chat"),
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages.length]);

  if (!user) {
    return <Spinner label="Log in to join the global chat." />;
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    send(text);
    setDraft("");
  };

  return (
    <div className="mx-auto flex h-dvh max-w-2xl flex-col px-4 py-4 md:py-6">
      <header className="mb-3 flex items-center justify-between">
        <h1 className="font-heading text-xl font-bold">Global Chat</h1>
        <span
          className={clsx(
            "flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium",
            status === "open" ? "bg-primary/10 text-primary" : "bg-coral/10 text-coral",
          )}
        >
          {status === "open" ? <Wifi size={14} aria-hidden="true" /> : <WifiOff size={14} aria-hidden="true" />}
          {status === "open" ? "Connected" : status === "connecting" ? "Connecting..." : "Disconnected"}
        </span>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto rounded-lg border border-border bg-surface p-3">
        {messages.length === 0 ? (
          <p className="py-8 text-center text-sm text-ink/50">No messages yet. Say hello!</p>
        ) : (
          <ul className="flex flex-col gap-3">
            {messages.map((message) => {
              const isMine = message.sender_id === user.id;
              return (
                <li key={message.id} className={clsx("flex flex-col", isMine ? "items-end" : "items-start")}>
                  <div
                    className={clsx(
                      "max-w-[80%] rounded-2xl px-3 py-2 text-sm",
                      isMine ? "bg-primary text-white" : "bg-canvas text-ink",
                      message.hidden && "italic opacity-60",
                    )}
                  >
                    {!isMine ? <p className="mb-0.5 text-xs font-semibold opacity-70">{message.sender_display_name}</p> : null}
                    <p>{message.text}</p>
                  </div>
                  {!isMine && !message.hidden ? (
                    <button
                      type="button"
                      onClick={() => reportMutation.mutate(message.id)}
                      className="mt-0.5 flex items-center gap-1 text-[11px] text-ink/40 hover:text-coral"
                    >
                      <Flag size={11} aria-hidden="true" />
                      Report
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {sendError ? <p className="mt-2 text-xs text-coral">{sendError}</p> : null}

      <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
        <label className="sr-only" htmlFor="chat-composer">
          Message
        </label>
        <input
          id="chat-composer"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          maxLength={1000}
          placeholder="Say something to fellow travellers..."
          className="flex-1 rounded-lg border border-border bg-surface px-3 py-2.5 text-sm focus:border-primary focus:outline-none"
        />
        <Button type="submit" disabled={!draft.trim()}>
          <Send size={16} aria-hidden="true" />
        </Button>
      </form>
    </div>
  );
}
