/** §10: DocumentTable status badges + delete action. */

import { fireEvent, render, screen } from "@testing-library/react";

import { DocumentTable } from "@/components/documents/DocumentTable";
import type { ApiDocument } from "@/lib/api/documents";

function doc(overrides: Partial<ApiDocument>): ApiDocument {
  return {
    id: "d1",
    filename: "report.pdf",
    mimeType: "application/pdf",
    sizeBytes: 2048,
    status: "ready",
    pageCount: 3,
    errorMessage: null,
    createdAt: "2026-07-09T10:00:00Z",
    ...overrides,
  };
}

test("renders one row per document with its status badge", () => {
  render(
    <DocumentTable
      documents={[
        doc({ id: "a", filename: "ready.pdf", status: "ready" }),
        doc({ id: "b", filename: "cooking.pdf", status: "processing" }),
        doc({ id: "c", filename: "broken.docx", status: "failed" }),
      ]}
      onDelete={jest.fn()}
    />,
  );
  expect(screen.getByText("Ready")).toBeInTheDocument();
  expect(screen.getByText("Processing…")).toBeInTheDocument();
  expect(screen.getByText("Failed")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "ready.pdf" })).toHaveAttribute(
    "href",
    "/documents/a",
  );
});

test("delete button reports the document id", () => {
  const onDelete = jest.fn();
  render(<DocumentTable documents={[doc({ id: "x9" })]} onDelete={onDelete} />);
  fireEvent.click(screen.getByRole("button", { name: "Delete" }));
  expect(onDelete).toHaveBeenCalledWith("x9");
});

test("formats file sizes for humans", () => {
  render(<DocumentTable documents={[doc({ sizeBytes: 5 * 1024 * 1024 })]} onDelete={jest.fn()} />);
  expect(screen.getByText("5.0 MB")).toBeInTheDocument();
});
