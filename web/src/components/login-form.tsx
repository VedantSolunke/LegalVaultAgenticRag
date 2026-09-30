"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import {
  AuthCard,
  authFieldClassName,
  authLabelClassName,
} from "@/components/auth-card";
import { AuthRedirectIfSignedIn } from "@/components/auth-redirect-if-signed-in";
import { requireAccessToken } from "@/lib/auth/session";
import { devBearerToken, supabaseConfigured } from "@/lib/config";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { signInWithToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const supabaseReady = supabaseConfigured();
  const devToken = devBearerToken();
  const resetSuccess = searchParams.get("reset") === "success";

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (supabaseReady) {
        const supabase = createSupabaseBrowserClient();
        const { data, error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) {
          throw signInError;
        }
        signInWithToken(requireAccessToken(data.session));
      } else if (devToken) {
        signInWithToken(devToken);
      } else {
        throw new Error("Configure Supabase or NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN");
      }
      router.replace("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  function useDevToken() {
    if (!devToken) {
      return;
    }
    signInWithToken(devToken);
    router.replace("/chat");
  }

  return (
    <>
      <AuthRedirectIfSignedIn />
      <AuthCard
        title="LegalVault"
        description="Sign in to research BNS provisions with cited sources."
        footer={
          supabaseReady ? (
            <p className="text-center text-sm text-slate-600">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="font-medium text-slate-900 underline">
                Create one
              </Link>
            </p>
          ) : undefined
        }
      >
        {resetSuccess && (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
            Password updated. Sign in with your new password.
          </p>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          {supabaseReady && (
            <>
              <label className={authLabelClassName}>
                Email
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={authFieldClassName}
                />
              </label>
              <label className={authLabelClassName}>
                Password
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={authFieldClassName}
                />
              </label>
              <p className="text-right text-sm">
                <Link
                  href="/forgot-password"
                  className="font-medium text-slate-700 underline"
                >
                  Forgot password?
                </Link>
              </p>
            </>
          )}

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {devToken && (
          <button
            type="button"
            onClick={useDevToken}
            className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            Continue with dev API token
          </button>
        )}

        {!supabaseReady && !devToken && (
          <p className="text-sm text-slate-600">
            Set <code className="text-xs">NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
            <code className="text-xs">NEXT_PUBLIC_SUPABASE_ANON_KEY</code>, or{" "}
            <code className="text-xs">NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN</code>{" "}
            for local development.
          </p>
        )}
      </AuthCard>
    </>
  );
}
