"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import { AuthCard } from "@/components/auth-card";
import { requireAccessToken } from "@/lib/auth/session";
import { supabaseConfigured } from "@/lib/config";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function AuthCallbackHandler() {
  const router = useRouter();
  const { signInWithToken } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!supabaseConfigured()) {
      setError("Supabase is not configured.");
      return;
    }

    let cancelled = false;

    async function completeAuth() {
      const supabase = createSupabaseBrowserClient();
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");

      try {
        if (code) {
          const { data, error: exchangeError } =
            await supabase.auth.exchangeCodeForSession(code);
          if (exchangeError) {
            throw exchangeError;
          }
          if (!cancelled && data.session) {
            signInWithToken(requireAccessToken(data.session));
            router.replace("/chat");
            return;
          }
        }

        const { data: sessionData, error: sessionError } =
          await supabase.auth.getSession();
        if (sessionError) {
          throw sessionError;
        }
        if (!cancelled && sessionData.session) {
          signInWithToken(requireAccessToken(sessionData.session));
          router.replace("/chat");
          return;
        }

        if (!cancelled) {
          setError("Could not complete sign-in. Try signing in from the login page.");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Sign-in failed");
        }
      }
    }

    void completeAuth();

    return () => {
      cancelled = true;
    };
  }, [router, signInWithToken]);

  return (
    <AuthCard
      title="LegalVault"
      description="Completing sign-in…"
    >
      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : (
        <p className="text-sm text-slate-600">Please wait.</p>
      )}
    </AuthCard>
  );
}
