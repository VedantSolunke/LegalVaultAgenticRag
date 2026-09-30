const STORAGE_KEY = "legalvault_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return sessionStorage.getItem(STORAGE_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(STORAGE_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}
