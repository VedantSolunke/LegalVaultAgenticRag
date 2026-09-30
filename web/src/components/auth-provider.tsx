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
import { fetchMe } from "@/lib/api/client";

type AuthContextValue = {
  accessToken: string | null;
  isAdmin: boolean;
  ready: boolean;
  signInWithToken: (token: string) => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setTokenState] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setTokenState(getAccessToken());
    setReady(true);
  }, []);

  useEffect(() => {
    if (!accessToken) {
      setIsAdmin(false);
      return;
    }
    let cancelled = false;
    fetchMe(accessToken)
      .then((profile) => {
        if (!cancelled) {
          setIsAdmin(profile.is_admin);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setIsAdmin(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  const signInWithToken = useCallback((token: string) => {
    setAccessToken(token);
    setTokenState(token);
  }, []);

  const signOut = useCallback(() => {
    clearAccessToken();
    setTokenState(null);
    setIsAdmin(false);
  }, []);

  const value = useMemo(
    () => ({ accessToken, isAdmin, ready, signInWithToken, signOut }),
    [accessToken, isAdmin, ready, signInWithToken, signOut],
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
