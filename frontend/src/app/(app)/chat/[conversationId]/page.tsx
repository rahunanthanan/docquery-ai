"use client";

/** §3.1 /chat/[conversationId]: ask questions, answers with citation panel. */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState, type FormEvent } from "react";

import { ChatWindow } from "@/components/chat/ChatWindow";
import { EmptyState } from "@/components/EmptyState";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { useAskQuestion, useConversation } from "@/hooks/useConversations";
import { useToast } from "@/providers/ToastProvider";

export default function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { toast } = useToast();
  const { data, isPending, isError, error } = useConversation(conversationId);
  const ask = useAskQuestion(conversationId);
  const [draft, setDraft] = useState("");

  if (isPending) return <SkeletonLoader lines={5} />;
  if (isError) {
    return (
      <EmptyState
        title="Couldn't load this conversation"
        detail={friendlyMessage(error)}
        action={
          <Link className="button" href="/chat">
            Back to chat
          </Link>
        }
      />
    );
  }

  const trimmed = draft.trim();
  const valid = trimmed.length >= 3 && trimmed.length <= 2000;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!valid || ask.isPending) return;
    ask.mutate(trimmed, {
      // §9: on failure the question was still saved — keep the draft so
      // the user can simply hit Ask again
      onSuccess: () => setDraft(""),
      onError: (err) => toast(friendlyMessage(err)),
    });
  }

  return (
    <div className="chat-page">
      <p>
        <Link href="/chat" className="muted">
          ← Conversations
        </Link>
      </p>
      <div className="page-header">
        <h1>{data.title}</h1>
      </div>

      <ChatWindow items={data.items} pendingText={ask.isPending ? ask.variables : null} />

      <form className="composer" onSubmit={handleSubmit}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask a question about your documents (3–2,000 characters)…"
          rows={2}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <button className="button" type="submit" disabled={!valid || ask.isPending}>
          {ask.isPending ? "Asking…" : "Ask"}
        </button>
      </form>
    </div>
  );
}
