/** §10: ChatWindow — bubbles, citation chips, notice + pending states. */

import { fireEvent, render, screen } from "@testing-library/react";

import { ChatWindow } from "@/components/chat/ChatWindow";
import type { Answer, QAItem } from "@/lib/api/qa";

function answer(overrides: Partial<Answer> = {}): Answer {
  return {
    id: "a1",
    content: "Revenue grew fourteen percent [1] and margins improved [9].",
    modelName: "fake-chat",
    promptTokens: 100,
    completionTokens: 20,
    costUsd: 0,
    latencyMs: 12,
    reviewStatus: "pending_review",
    createdAt: "2026-07-09T10:00:00Z",
    citations: [
      {
        marker: 1,
        documentId: "doc-1",
        page: 3,
        snippet: "Revenue grew fourteen percent year over year.",
        similarity: 0.71,
      },
    ],
    ...overrides,
  };
}

function item(a: Answer | null): QAItem {
  return {
    question: { id: "q1", text: "How did revenue do?", createdAt: "2026-07-09T10:00:00Z" },
    answer: a,
  };
}

test("renders question and answer bubbles", () => {
  render(<ChatWindow items={[item(answer())]} />);
  expect(screen.getByText("How did revenue do?")).toBeInTheDocument();
  expect(screen.getByText(/Revenue grew fourteen percent/)).toBeInTheDocument();
  expect(screen.getByText("Pending review")).toBeInTheDocument();
});

test("clicking a citation chip opens the source card with page number", () => {
  render(<ChatWindow items={[item(answer())]} />);
  expect(screen.queryByText(/Page 3/)).not.toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Citation 1" }));
  expect(screen.getByText(/Page 3/)).toBeInTheDocument();
  expect(
    screen.getByText("Revenue grew fourteen percent year over year."),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "Citation 1" }));
  expect(screen.queryByText(/Page 3/)).not.toBeInTheDocument();
});

test("markers without stored citations stay plain text, not chips", () => {
  render(<ChatWindow items={[item(answer())]} />);
  expect(screen.queryByRole("button", { name: "Citation 9" })).not.toBeInTheDocument();
  expect(screen.getByText(/\[9\]/)).toBeInTheDocument();
});

test("a question without an answer renders the no-grounded-answer notice", () => {
  render(<ChatWindow items={[item(null)]} />);
  expect(
    screen.getByText("No grounded answer was found in your documents."),
  ).toBeInTheDocument();
});

test("a pending question shows an echo bubble with a thinking indicator", () => {
  render(<ChatWindow items={[]} pendingText="What about margins?" />);
  expect(screen.getByText("What about margins?")).toBeInTheDocument();
  expect(screen.getByText("Thinking…")).toBeInTheDocument();
});
