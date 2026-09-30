import { afterEach, describe, expect, it } from "vitest";

import { authCallbackUrl, resetPasswordRedirectUrl, siteUrl } from "@/lib/config";

const ORIGINAL_SITE_URL = process.env.NEXT_PUBLIC_SITE_URL;

afterEach(() => {
  if (ORIGINAL_SITE_URL === undefined) {
    delete process.env.NEXT_PUBLIC_SITE_URL;
  } else {
    process.env.NEXT_PUBLIC_SITE_URL = ORIGINAL_SITE_URL;
  }
});

describe("siteUrl", () => {
  it("uses NEXT_PUBLIC_SITE_URL without a trailing slash", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "https://legalvault.example/";
    expect(siteUrl()).toBe("https://legalvault.example");
  });

  it("falls back to localhost when env is unset", () => {
    delete process.env.NEXT_PUBLIC_SITE_URL;
    expect(siteUrl()).toBe("http://localhost:3000");
  });
});

describe("auth redirect URLs", () => {
  it("builds callback and reset-password paths from site URL", () => {
    process.env.NEXT_PUBLIC_SITE_URL = "http://localhost:3000";
    expect(authCallbackUrl()).toBe("http://localhost:3000/auth/callback");
    expect(resetPasswordRedirectUrl()).toBe("http://localhost:3000/reset-password");
  });
});
