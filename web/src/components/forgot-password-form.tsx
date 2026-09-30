"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import {
  AuthCard,
  authFieldClassName,
  authLabelClassName,
} from "@/components/auth-card";
import { AuthRedirectIfSignedIn } from "@/components/auth-redirect-if-signed-in";
import { resetPasswordRedirectUrl, supabaseConfigured } from "@/lib/config";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const supabaseReady = supabaseConfigured();

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!supabaseReady) {
      setError("Configure Supabase to reset your password.");
      return;
    }

    setLoading(true);
    try {
      const supabase = createSupabaseBrowserClient();
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: resetPasswordRedirectUrl(),
      });
      if (resetError) {
        throw resetError;
      }
      setSent(true);
      setEmail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send reset email");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <AuthRedirectIfSignedIn />
      <AuthCard
        title="LegalVault"
        description="We will email you a link to reset your password."
        footer={
          <p className="text-center text-sm text-slate-600">
            <Link href="/login" className="font-medium text-slate-900 underline">
              Back to sign in
            </Link>
          </p>
        }
      >
        {sent ? (
          <p className="text-sm text-slate-700">
            If an account exists for that email, you will receive a reset link shortly.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="space-y-4">
            {supabaseReady ? (
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
            ) : (
              <p className="text-sm text-slate-600">
                Set <code className="text-xs">NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
                <code className="text-xs">NEXT_PUBLIC_SUPABASE_ANON_KEY</code>.
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
              {loading ? "Sending…" : "Send reset link"}
            </button>
          </form>
        )}
      </AuthCard>
    </>
  );
}
