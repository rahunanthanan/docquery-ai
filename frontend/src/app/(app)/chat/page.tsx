"use client";

/** §3.1 /chat: conversation list + start a new conversation. */

import Link from "next/link";
import { useRouter } from "next/navigation";

import { EmptyState } from "@/components/EmptyState";
import { SkeletonLoader } from "@/components/SkeletonLoader";
import { friendlyMessage } from "@/lib/errorMessages";
import { formatDate } from "@/lib/format";
import { useConversations, useCreateConversation } from "@/hooks/useConversations";
import { useToast } from "@/providers/ToastProvider";

export default function ChatPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { data, isPending, isError, error, refetch } = useConversations();
  const create = useCreateConversation();

  function startConversation() {
    create.mutate(undefined, {
      onSuccess: (conversation) => router.push(`/chat/${conversation.id}`),
      onError: (err) => toast(friendlyMessage(err)),
    });
  }

  return (
    <div>
      <div className="page-header">
        <h1>Chat</h1>
        <button className="button" onClick={startConversation} disabled={create.isPending}>
          {create.isPending ? "Starting…" : "New conversation"}
        </button>
      </div>

      {isPending ? (
        <SkeletonLoader lines={4} />
      ) : isError ? (
        <EmptyState
          title="Couldn't load your conversations"
          detail={friendlyMessage(error)}
          action={
            <button className="button" onClick={() => void refetch()}>
              Try again
            </button>
          }
        />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No conversations yet"
          detail="Start one and ask questions about your uploaded documents."
        />
      ) : (
        <ul className="conversation-list">
          {data.items.map((conversation) => (
            <li key={conversation.id}>
              <Link href={`/chat/${conversation.id}`} className="conversation-item">
                <span>{conversation.title}</span>
                <span className="muted">{formatDate(conversation.createdAt)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
