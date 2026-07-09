/**
 * §10: api service parsing — envelope → ApiError, silent refresh → retry
 * once, session-expired handler on refresh failure.
 */

import { z } from "zod";

import {
  ApiError,
  apiFetch,
  setAccessToken,
  setOnSessionExpired,
  setOnTokenRefreshed,
} from "@/lib/api/client";

const fetchMock = jest.fn();
global.fetch = fetchMock as unknown as typeof fetch;

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status < 400,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

const TOKEN_BODY = {
  accessToken: "new-token",
  tokenType: "bearer",
  expiresIn: 900,
  user: {
    id: "u1",
    email: "a@b.c",
    fullName: "A",
    role: "user",
    isActive: true,
  },
};

beforeEach(() => {
  fetchMock.mockReset();
  setAccessToken(null);
  setOnSessionExpired(null);
  setOnTokenRefreshed(null);
});

test("parses successful responses through the zod schema", async () => {
  fetchMock.mockResolvedValueOnce(jsonResponse(200, { value: 42 }));
  const result = await apiFetch("/api/v1/thing", z.object({ value: z.number() }));
  expect(result).toEqual({ value: 42 });
});

test("error envelope becomes ApiError with code and requestId", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse(404, {
      error: { code: "DOCUMENT_NOT_FOUND", message: "Document not found.", requestId: "r1" },
    }),
  );
  const promise = apiFetch("/api/v1/documents/x", z.unknown());
  await expect(promise).rejects.toMatchObject({
    code: "DOCUMENT_NOT_FOUND",
    status: 404,
    requestId: "r1",
  });
  await expect(promise).rejects.toBeInstanceOf(ApiError);
});

test("401 triggers one silent refresh then retries the request", async () => {
  const refreshed = jest.fn();
  setOnTokenRefreshed(refreshed);
  fetchMock
    .mockResolvedValueOnce(jsonResponse(401, { error: { code: "TOKEN_EXPIRED", message: "x" } }))
    .mockResolvedValueOnce(jsonResponse(200, TOKEN_BODY)) // the refresh call
    .mockResolvedValueOnce(jsonResponse(200, { value: 7 })); // the retry

  const result = await apiFetch("/api/v1/thing", z.object({ value: z.number() }));

  expect(result).toEqual({ value: 7 });
  expect(refreshed).toHaveBeenCalledWith(expect.objectContaining({ accessToken: "new-token" }));
  const retryHeaders = fetchMock.mock.calls[2][1].headers as Record<string, string>;
  expect(retryHeaders.Authorization).toBe("Bearer new-token");
});

test("failed refresh calls the session-expired handler and throws", async () => {
  const expired = jest.fn();
  setOnSessionExpired(expired);
  fetchMock
    .mockResolvedValueOnce(jsonResponse(401, { error: { code: "TOKEN_EXPIRED", message: "x" } }))
    .mockResolvedValueOnce(jsonResponse(401, { error: { code: "NOT_AUTHENTICATED", message: "x" } }));

  await expect(apiFetch("/api/v1/thing", z.unknown())).rejects.toBeInstanceOf(ApiError);
  expect(expired).toHaveBeenCalledTimes(1);
  expect(fetchMock).toHaveBeenCalledTimes(2); // no retry after failed refresh
});

test("auth endpoints never trigger the refresh loop", async () => {
  fetchMock.mockResolvedValueOnce(
    jsonResponse(401, { error: { code: "INVALID_CREDENTIALS", message: "nope" } }),
  );
  await expect(
    apiFetch("/api/v1/auth/login", z.unknown(), { method: "POST", body: {} }),
  ).rejects.toMatchObject({ code: "INVALID_CREDENTIALS" });
  expect(fetchMock).toHaveBeenCalledTimes(1);
});
