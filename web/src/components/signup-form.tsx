"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import {
  AuthCard,
  authFieldClassName,
  authLabelClassName,
} from "@/components/auth-card";
import { AuthRedirectIfSignedIn } from "@/components/auth-redirect-if-signed-in";
import { requireAccessToken } from "@/lib/auth/session";
import { authCallbackUrl, supabaseConfigured } from "@/lib/config";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const MIN_PASSWORD_LENGTH = 6;

export function SignupForm() {
  const router = useRouter();
  const { signInWithToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);

  const supabaseReady = supabaseConfigured();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (!supabaseReady) {
      setError("Configure Supabase to create an account.");
      return;
    }

    setLoading(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: authCallbackUrl(),
        },
      });
      if (signUpError) {
        throw signUpError;
      }

      if (data.session) {
        signInWithToken(requireAccessToken(data.session));
        router.replace("/chat");
        return;
      }

      setAwaitingConfirmation(true);
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <AuthRedirectIfSignedIn />
      <AuthCard
        title="LegalVault"
        description="Create an account to research BNS provisions with cited sources."
        footer={
          <p className="text-center text-sm text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-slate-900 underline">
              Sign in
            </Link>
          </p>
        }
      >
        {awaitingConfirmation ? (
          <div className="space-y-3 text-sm text-slate-700">
            <p>
              Check your email for a confirmation link. After confirming, you will be
              signed in automatically.
            </p>
            <p>
              <Link href="/login" className="font-medium text-slate-900 underline">
                Back to sign in
              </Link>
            </p>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            {supabaseReady ? (
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
                    minLength={MIN_PASSWORD_LENGTH}
                    autoComplete="new-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={authFieldClassName}
                  />
                </label>
                <label className={authLabelClassName}>
                  Confirm password
                  <input
                    type="password"
                    required
                    minLength={MIN_PASSWORD_LENGTH}
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={authFieldClassName}
                  />
                </label>
              </>
            ) : (
              <p className="text-sm text-slate-600">
                Set <code className="text-xs">NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
                <code className="text-xs">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> to sign
                up.
              </p>
            )}

            {error && (
              <p className="text-sm text-red-600" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !supabaseReady}
              className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>
        )}
      </AuthCard>
    </>
  );
}
