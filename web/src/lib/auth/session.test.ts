import { describe, expect, it } from "vitest";

import { requireAccessToken } from "@/lib/auth/session";

describe("requireAccessToken", () => {
  it("returns the access token when present", () => {
    expect(
      requireAccessToken({
        access_token: "jwt-token",
        token_type: "bearer",
        expires_in: 3600,
        expires_at: 0,
        refresh_token: "refresh",
        user: {} as never,
      }),
    ).toBe("jwt-token");
  });

  it("throws when session is missing a token", () => {
    expect(() => requireAccessToken(null)).toThrow("No access token");
  });
});
