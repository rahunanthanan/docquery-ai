/** §10: CitationCard — snippet, page number and document link. */

import { render, screen } from "@testing-library/react";

import { CitationCard } from "@/components/chat/CitationCard";

const CITATION = {
  marker: 2,
  documentId: "doc-42",
  page: 7,
  snippet: "Quarterly revenue grew fourteen percent year over year.",
  similarity: 0.734,
};

test("shows marker, page, similarity and the source snippet", () => {
  render(<CitationCard citation={CITATION} />);
  expect(screen.getByText("[2]")).toBeInTheDocument();
  expect(screen.getByText(/Page 7/)).toBeInTheDocument();
  expect(screen.getByText(/similarity 0.73/)).toBeInTheDocument();
  expect(
    screen.getByText("Quarterly revenue grew fourteen percent year over year."),
  ).toBeInTheDocument();
});

test("links to the cited document", () => {
  render(<CitationCard citation={CITATION} />);
  expect(screen.getByRole("link", { name: "Open document" })).toHaveAttribute(
    "href",
    "/documents/doc-42",
  );
});
