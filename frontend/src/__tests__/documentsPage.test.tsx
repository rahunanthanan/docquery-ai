/** §10: the documents page renders explicit loading, empty and error states. */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";

import DocumentsPage from "@/app/(app)/documents/page";
import { ToastProvider } from "@/providers/ToastProvider";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/documents",
}));

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function renderPage() {
  // retries disabled so the error state appears without retry delays
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <DocumentsPage />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => fetchMock.mockReset());

test("shows the empty state when there are no documents", async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve({ items: [], total: 0, limit: 20, offset: 0 }),
  } as Response);
  renderPage();
  expect(await screen.findByText("No documents yet")).toBeInTheDocument();
});

test("shows the error state with a retry action when loading fails", async () => {
  fetchMock.mockResolvedValue({
    ok: false,
    status: 500,
    json: () =>
      Promise.resolve({ error: { code: "INTERNAL_ERROR", message: "boom", requestId: "r" } }),
  } as Response);
  renderPage();
  expect(await screen.findByText("Couldn't load your documents")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
});

test("renders the table when documents exist", async () => {
  fetchMock.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () =>
      Promise.resolve({
        items: [
          {
            id: "d1",
            filename: "q3-report.md",
            mimeType: "text/markdown",
            sizeBytes: 300,
            status: "ready",
            pageCount: 1,
            errorMessage: null,
            createdAt: "2026-07-09T10:00:00Z",
          },
        ],
        total: 1,
        limit: 20,
        offset: 0,
      }),
  } as Response);
  renderPage();
  expect(await screen.findByRole("link", { name: "q3-report.md" })).toBeInTheDocument();
  expect(screen.getByText("Ready")).toBeInTheDocument();
});
