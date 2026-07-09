/**
 * Typed fetch wrapper (§3.3): components never call fetch directly.
 *
 * - Access token lives in memory only; the refresh token is an httpOnly
 *   cookie the browser attaches itself (credentials: "include").
 * - §9: a 401 triggers one silent refresh + retry; if that fails the
 *   session-expired handler (set by AuthProvider) redirects to /login.
 * - Error responses use the backend envelope and become ApiError.
 */

import { z } from "zod";

import { tokenResponseSchema, type TokenResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let accessToken: string | null = null;
let onSessionExpired: (() => void) | null = null;
let onTokenRefreshed: ((result: TokenResponse) => void) | null = null;

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setOnSessionExpired(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

export function setOnTokenRefreshed(handler: ((result: TokenResponse) => void) | null): void {
  onTokenRefreshed = handler;
}

const errorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    requestId: z.string().optional(),
  }),
});

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = errorEnvelopeSchema.parse(await response.json());
    return new ApiError(
      body.error.code,
      body.error.message,
      response.status,
      body.error.requestId,
    );
  } catch {
    return new ApiError("UNKNOWN", `Request failed with status ${response.status}.`, response.status);
  }
}

/** One silent refresh attempt; updates the in-memory token on success. */
export async function tryRefresh(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) return false;
    const result = tokenResponseSchema.parse(await response.json());
    accessToken = result.accessToken;
    onTokenRefreshed?.(result);
    return true;
  } catch {
    return false;
  }
}

export interface ApiFetchOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  /** multipart uploads pass FormData and skip the JSON content type */
  formData?: FormData;
  /** internal: prevents a second refresh loop on the retried request */
  retryOn401?: boolean;
}

export async function apiFetch<T>(
  path: string,
  schema: z.ZodType<T>,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { method = "GET", body, formData, retryOn401 = true } = options;
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    credentials: "include",
    body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
  });

  if (response.status === 401 && retryOn401 && !path.startsWith("/api/v1/auth/")) {
    if (await tryRefresh()) {
      return apiFetch(path, schema, { ...options, retryOn401: false });
    }
    onSessionExpired?.();
    throw await toApiError(response);
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return schema.parse(undefined);
  return schema.parse(await response.json());
}
