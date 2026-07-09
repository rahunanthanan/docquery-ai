/** §10: form validation + error-state rendering with friendly copy. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import LoginPage from "@/app/(auth)/login/page";
import { AuthProvider } from "@/providers/AuthProvider";
import { ToastProvider } from "@/providers/ToastProvider";

const push = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: jest.fn() }),
  usePathname: () => "/login",
}));

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function jsonResponse(status: number, body: unknown): Response {
  return { ok: status < 400, status, json: () => Promise.resolve(body) } as Response;
}

function renderLogin() {
  // AuthProvider mounts with a refresh attempt — fail it (anonymous session)
  fetchMock.mockResolvedValueOnce(
    jsonResponse(401, { error: { code: "NOT_AUTHENTICATED", message: "x" } }),
  );
  return render(
    <ToastProvider>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </ToastProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  push.mockReset();
});

test("submit is disabled until the form is valid", async () => {
  renderLogin();
  const submit = screen.getByRole("button", { name: "Log in" });
  expect(submit).toBeDisabled();

  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.co" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "pw" } });
  await waitFor(() => expect(submit).toBeEnabled());
});

test("invalid email shows an inline error after blur", async () => {
  renderLogin();
  const email = screen.getByLabelText("Email");
  fireEvent.change(email, { target: { value: "not-an-email" } });
  fireEvent.blur(email);
  expect(await screen.findByText("Enter a valid email address.")).toBeInTheDocument();
});

test("wrong credentials render the friendly error message", async () => {
  renderLogin();
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "a@b.co" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong-pass" } });

  fetchMock.mockResolvedValueOnce(
    jsonResponse(401, { error: { code: "INVALID_CREDENTIALS", message: "raw server text" } }),
  );
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));

  expect(
    await screen.findAllByText("That email and password combination doesn't match."),
  ).not.toHaveLength(0);
  expect(push).not.toHaveBeenCalled();
});
