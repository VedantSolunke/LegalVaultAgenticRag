import type { Session } from "@supabase/supabase-js";

export function requireAccessToken(session: Session | null): string {
  const token = session?.access_token;
  if (!token) {
    throw new Error("No access token returned from Supabase");
  }
  return token;
}
