"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth/token";

type AuthContextValue = {
  accessToken: string | null;
  ready: boolean;
  signInWithToken: (token: string) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setTokenState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setTokenState(getAccessToken());
    setReady(true);
  }, []);

  const signInWithToken = useCallback((token: string) => {
    setAccessToken(token);
    setTokenState(token);
  }, []);

  const signOut = useCallback(() => {
    clearAccessToken();
    setTokenState(null);
  }, []);

  const value = useMemo(
    () => ({ accessToken, ready, signInWithToken, signOut }),
    [accessToken, ready, signInWithToken, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
