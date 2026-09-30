"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/auth-provider";
import {
  AuthCard,
  authFieldClassName,
  authLabelClassName,
} from "@/components/auth-card";
import { requireAccessToken } from "@/lib/auth/session";
import { supabaseConfigured } from "@/lib/config";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

const MIN_PASSWORD_LENGTH = 6;

export function ResetPasswordForm() {
  const router = useRouter();
  const { signInWithToken } = useAuth();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [recoveryReady, setRecoveryReady] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);

  const supabaseReady = supabaseConfigured();

  useEffect(() => {
    if (!supabaseReady) {
      setCheckingSession(false);
      return;
    }

    const supabase = createSupabaseBrowserClient();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY" || event === "SIGNED_IN") {
        setRecoveryReady(true);
        setCheckingSession(false);
      }
    });

    void supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        setRecoveryReady(true);
      }
      setCheckingSession(false);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [supabaseReady]);

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
      setError("Configure Supabase to reset your password.");
      return;
    }

    setLoading(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { error: updateError } = await supabase.auth.updateUser({ password });
      if (updateError) {
        throw updateError;
      }

      const { data: sessionData, error: sessionError } = await supabase.auth.getSession();
      if (sessionError) {
        throw sessionError;
      }

      const token = sessionData.session?.access_token;
      if (token) {
        signInWithToken(requireAccessToken(sessionData.session));
        router.replace("/chat");
        return;
      }

      router.replace("/login?reset=success");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard
      title="LegalVault"
      description="Choose a new password for your account."
      footer={
        <p className="text-center text-sm text-slate-600">
          <Link href="/login" className="font-medium text-slate-900 underline">
            Back to sign in
          </Link>
        </p>
      }
    >
      {checkingSession ? (
        <p className="text-sm text-slate-600">Loading…</p>
      ) : !recoveryReady ? (
        <p className="text-sm text-slate-700">
          Open the reset link from your email to set a new password.{" "}
          <Link href="/forgot-password" className="font-medium text-slate-900 underline">
            Request a new link
          </Link>
        </p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <label className={authLabelClassName}>
            New password
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
            Confirm new password
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
            {loading ? "Updating…" : "Update password"}
          </button>
        </form>
      )}
    </AuthCard>
  );
}
