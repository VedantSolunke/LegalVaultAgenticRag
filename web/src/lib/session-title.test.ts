import { describe, expect, it } from "vitest";

import { displaySessionTitle } from "@/lib/session-title";

describe("displaySessionTitle", () => {
  it("uses New chat when title is empty", () => {
    expect(displaySessionTitle(null)).toBe("New chat");
    expect(displaySessionTitle("   ")).toBe("New chat");
  });

  it("truncates long titles", () => {
    const long = "a".repeat(80);
    const displayed = displaySessionTitle(long);
    expect(displayed.length).toBe(48);
    expect(displayed.endsWith("…")).toBe(true);
  });
});
