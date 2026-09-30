export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_LEGALVAULT_API_URL ?? "http://localhost:8000";
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
