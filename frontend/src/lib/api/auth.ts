import { z } from "zod";

import { apiFetch } from "./client";
import { tokenResponseSchema, userSchema, type ApiUser, type TokenResponse } from "./types";

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch("/api/v1/auth/login", tokenResponseSchema, {
    method: "POST",
    body: { email, password },
  });
}

export function register(
  email: string,
  password: string,
  fullName: string,
): Promise<ApiUser> {
  return apiFetch("/api/v1/auth/register", userSchema, {
    method: "POST",
    body: { email, password, fullName },
  });
}

export function logout(): Promise<void> {
  return apiFetch("/api/v1/auth/logout", z.void(), { method: "POST" });
}
