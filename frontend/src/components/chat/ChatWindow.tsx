"use client";

import { useEffect, useRef } from "react";

import {
  AnswerBubble,
  NoticeBubble,
  QuestionBubble,
} from "@/components/chat/MessageBubble";
import type { QAItem } from "@/lib/api/qa";

interface Props {
  items: QAItem[];
  /** question currently in flight — echoed with a thinking indicator */
  pendingText?: string | null;
}

export function ChatWindow({ items, pendingText }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
  }, [items.length, pendingText]);

  return (
    <div className="chat-window">
      {items.length === 0 && !pendingText ? (
        <NoticeBubble>
          Ask a question about your documents — answers cite their sources.
        </NoticeBubble>
      ) : null}
      {items.map((item) => (
        <div key={item.question.id} className="chat-item">
          <QuestionBubble text={item.question.text} />
          {item.answer !== null ? (
            <AnswerBubble answer={item.answer} />
          ) : (
            <NoticeBubble>
              No grounded answer was found in your documents.
            </NoticeBubble>
          )}
        </div>
      ))}
      {pendingText ? (
        <div className="chat-item">
          <QuestionBubble text={pendingText} />
          <div className="bubble bubble-answer muted" aria-label="Thinking">
            Thinking…
          </div>
        </div>
      ) : null}
      <div ref={bottomRef} />
    </div>
  );
}
