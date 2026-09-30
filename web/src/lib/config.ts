const DEFAULT_SITE_URL = "http://localhost:3000";

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_LEGALVAULT_API_URL ?? "http://localhost:8000";
}

export function siteUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_SITE_URL?.trim();
  if (fromEnv) {
    return fromEnv.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return DEFAULT_SITE_URL;
}

export function authCallbackUrl(): string {
  return `${siteUrl()}/auth/callback`;
}

export function resetPasswordRedirectUrl(): string {
  return `${siteUrl()}/reset-password`;
}

export function supabaseConfigured(): boolean {
  return Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  );
}

export function devBearerToken(): string | null {
  return process.env.NEXT_PUBLIC_LEGALVAULT_DEV_BEARER_TOKEN ?? null;
}
