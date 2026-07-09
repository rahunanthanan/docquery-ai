/** §10: client-side upload validation — no network call for bad files. */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { DocumentUploader } from "@/components/documents/DocumentUploader";
import { ToastProvider } from "@/providers/ToastProvider";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function renderUploader() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: 0 } } });
  return render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <DocumentUploader />
      </ToastProvider>
    </QueryClientProvider>,
  );
}

function fileInput(): HTMLInputElement {
  return document.querySelector('input[type="file"]') as HTMLInputElement;
}

beforeEach(() => fetchMock.mockReset());

test("rejects unsupported file types without calling the API", async () => {
  renderUploader();
  const png = new File(["fake"], "photo.png", { type: "image/png" });
  fireEvent.change(fileInput(), { target: { files: [png] } });

  expect(
    await screen.findByText(/only PDF, DOCX, TXT and Markdown files are supported/),
  ).toBeInTheDocument();
  expect(fetchMock).not.toHaveBeenCalled();
});

test("rejects files over 20 MB without calling the API", async () => {
  renderUploader();
  const big = new File(["x"], "big.pdf", { type: "application/pdf" });
  Object.defineProperty(big, "size", { value: 21 * 1024 * 1024 });
  fireEvent.change(fileInput(), { target: { files: [big] } });

  expect(await screen.findByText(/files must be 20 MB or smaller/)).toBeInTheDocument();
  expect(fetchMock).not.toHaveBeenCalled();
});

test("uploads a valid file and reports success", async () => {
  renderUploader();
  fetchMock.mockResolvedValueOnce({
    ok: true,
    status: 202,
    json: () =>
      Promise.resolve({
        id: "d1",
        filename: "report.pdf",
        mimeType: "application/pdf",
        sizeBytes: 4,
        status: "uploaded",
        pageCount: null,
        errorMessage: null,
        createdAt: "2026-07-09T00:00:00Z",
      }),
  } as Response);

  const pdf = new File(["%PDF"], "report.pdf", { type: "application/pdf" });
  fireEvent.change(fileInput(), { target: { files: [pdf] } });

  expect(await screen.findByText("report.pdf uploaded — processing.")).toBeInTheDocument();
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toContain("/api/v1/documents");
  expect(init.body).toBeInstanceOf(FormData);
});
