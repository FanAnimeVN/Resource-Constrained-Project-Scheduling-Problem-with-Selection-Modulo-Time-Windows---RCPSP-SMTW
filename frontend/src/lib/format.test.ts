import { describe, expect, it } from "vitest";

import { blockKind, nextTerms, pct, termLabel } from "./format";

describe("format", () => {
  it("định dạng nhãn học kỳ", () => {
    expect(termLabel({ year: 2026, kind: "HK1" })).toBe("HK1 2026–2027");
    expect(termLabel({ year: 2026, kind: "HE" })).toBe("Hè 2027");
  });

  it("sinh dãy học kỳ có/không có hè", () => {
    expect(nextTerms({ year: 2026, kind: "HK2" }, 3).map(termLabel)).toEqual([
      "HK2 2026–2027",
      "HK1 2027–2028",
      "HK2 2027–2028",
    ]);
    expect(nextTerms({ year: 2026, kind: "HK2" }, 2, true).map(termLabel)).toEqual(["HK2 2026–2027", "Hè 2027"]);
  });

  it("phần trăm và màu khối", () => {
    expect(pct(0.756)).toBe("76%");
    expect(pct(null)).toBe("–");
    expect(blockKind("unknown").label).toBe("Khác");
  });
});
