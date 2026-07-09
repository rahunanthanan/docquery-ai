"use client";

/**
 * Auth context (§3.3): access token in memory, user in state.
 * On mount it attempts one silent refresh (httpOnly cookie) to restore
 * the session; the API client calls back here on refresh and expiry.
 */

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import * as authApi from "@/lib/api/auth";
import {
  setAccessToken,
  setOnSessionExpired,
  setOnTokenRefreshed,
  tryRefresh,
} from "@/lib/api/client";
import type { ApiUser } from "@/lib/api/types";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  user: ApiUser | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<ApiUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    setOnTokenRefreshed((result) => {
      setUser(result.user);
      setStatus("authenticated");
    });
    setOnSessionExpired(() => {
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
      router.push("/login");
    });
    void tryRefresh().then((restored) => {
      if (!restored) setStatus("anonymous");
      // success path is handled by the onTokenRefreshed callback
    });
    return () => {
      setOnTokenRefreshed(null);
      setOnSessionExpired(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const result = await authApi.login(email, password);
    setAccessToken(result.accessToken);
    setUser(result.user);
    setStatus("authenticated");
  }, []);

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      await authApi.register(email, password, fullName);
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      setUser(null);
      setStatus("anonymous");
      router.push("/login");
    }
  }, [router]);

  const value = useMemo(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
