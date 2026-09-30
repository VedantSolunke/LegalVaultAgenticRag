import { describe, expect, it } from "vitest";

import { formatQueryMode } from "@/lib/api/client";

describe("formatQueryMode", () => {
  it("replaces underscores with spaces for display", () => {
    expect(formatQueryMode("section_lookup")).toBe("section lookup");
    expect(formatQueryMode("fact_pattern_analysis")).toBe("fact pattern analysis");
  });
});
