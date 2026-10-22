export const BLOCK_KIND: Record<string, { label: string; card: string; dot: string }> = {
  general: { label: "Đại cương", card: "border-sky-200 bg-sky-50", dot: "bg-sky-500" },
  foundation: { label: "Cơ sở ngành", card: "border-violet-200 bg-violet-50", dot: "bg-violet-500" },
  major: { label: "Chuyên ngành", card: "border-emerald-200 bg-emerald-50", dot: "bg-emerald-500" },
  free: { label: "Tự chọn tự do", card: "border-amber-200 bg-amber-50", dot: "bg-amber-500" },
  graduation: { label: "Tốt nghiệp", card: "border-rose-200 bg-rose-50", dot: "bg-rose-500" },
  other: { label: "Khác", card: "border-slate-200 bg-white", dot: "bg-slate-400" },
};

export const blockKind = (kind?: string | null) => BLOCK_KIND[kind ?? "other"] ?? BLOCK_KIND.other;

export const STRATEGY_COLOR: Record<string, string> = {
  PERSONALIZED: "#1d4ed8",
  FAST_TRACK: "#dc2626",
  BALANCED: "#059669",
  RISK_AVERSE: "#d97706",
  SPECIALIZATION_FOCUS: "#7c3aed",
};

export const STRATEGY_HINT: Record<string, string> = {
  PERSONALIZED: "Dung hòa các mục tiêu theo trọng số bạn chọn.",
  FAST_TRACK: "Ra trường sớm nhất có thể, tải mỗi kỳ cao.",
  BALANCED: "Tải đều các kỳ, tốt nghiệp đúng tiến độ chuẩn.",
  RISK_AVERSE: "Học sớm môn nút cổ chai để còn đường học lại nếu rớt.",
  SPECIALIZATION_FOCUS: "Chọn môn tự chọn tập trung theo sở thích.",
};

export const BADGE_STYLE: Record<string, string> = {
  găng: "bg-red-100 text-red-700",
  "mở 1 lần/năm": "bg-amber-100 text-amber-800",
  "mở 2 năm/lần": "bg-orange-100 text-orange-800",
  "rủi ro": "bg-purple-100 text-purple-700",
  "học lại": "bg-slate-200 text-slate-700",
};

export const STATUS_LABEL: Record<string, string> = {
  PASSED: "Đạt",
  FAILED: "Rớt",
  EXEMPTED: "Miễn",
  IN_PROGRESS: "Đang học",
};

export const KIND_LABEL: Record<string, string> = { HK1: "HK1", HK2: "HK2", HE: "Hè" };

export function termLabel(t: { year: number; kind: string }): string {
  if (t.kind === "HE") return `Hè ${t.year + 1}`;
  return `${t.kind} ${t.year}–${t.year + 1}`;
}

export function pct(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined) return "–";
  return `${(x * 100).toFixed(digits)}%`;
}

export function nextTerms(start: { year: number; kind: string }, n: number, summer = false) {
  const out: { year: number; kind: "HK1" | "HK2" | "HE" }[] = [];
  let cur = { ...start } as { year: number; kind: "HK1" | "HK2" | "HE" };
  for (let i = 0; i < n; i++) {
    out.push(cur);
    if (cur.kind === "HK1") cur = { year: cur.year, kind: "HK2" };
    else if (cur.kind === "HK2") cur = summer ? { year: cur.year, kind: "HE" } : { year: cur.year + 1, kind: "HK1" };
    else cur = { year: cur.year + 1, kind: "HK1" };
  }
  return out;
}
