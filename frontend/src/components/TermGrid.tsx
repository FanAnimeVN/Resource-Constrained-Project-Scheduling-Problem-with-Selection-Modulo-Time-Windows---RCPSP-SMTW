import type { Plan, ScheduledCourse } from "../api/types";
import { blockKind } from "../lib/format";
import { Badge } from "./ui";

interface Props {
  plan: Plan;
  onSelect: (c: ScheduledCourse, termLabel: string) => void;
  selectedId?: string | null;
}

export default function TermGrid({ plan, onSelect, selectedId }: Props) {
  return (
    <div className="overflow-x-auto pb-2" data-testid="term-grid">
      <div className="flex gap-3">
        {plan.terms.map((t) => {
          const max = t.max_credits;
          const ratio = Math.min(1, t.credits / Math.max(1, max));
          const below = t.min_credits !== null && t.min_credits !== undefined && t.credits < t.min_credits;
          return (
            <section key={t.index} className={`w-56 shrink-0 rounded-xl border ${t.is_main ? "border-slate-200 bg-white" : "border-dashed border-amber-300 bg-amber-50/40"}`}>
              <header className="border-b border-slate-100 px-3 py-2">
                <div className="flex items-baseline justify-between">
                  <h3 className="text-sm font-semibold text-slate-800">{t.label}</h3>
                  <span className={`text-xs font-semibold ${below ? "text-red-600" : "text-slate-600"}`}>{t.credits} TC</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100" title={`Giới hạn ${t.min_credits ?? 0}–${max} TC`}>
                  <div className="h-full rounded-full bg-blue-600" style={{ width: `${ratio * 100}%` }} />
                </div>
                <div className="mt-1 text-[10px] text-slate-400">
                  {t.is_main ? `Giới hạn ${t.min_credits ?? 0}–${max} TC` : `Học kỳ hè, tối đa ${max} TC`}
                </div>
              </header>
              <ul className="flex flex-col gap-2 p-2">
                {t.courses.map((c) => {
                  const kind = blockKind(c.block_kind);
                  return (
                    <li key={c.course_id}>
                      <button
                        type="button"
                        onClick={() => onSelect(c, t.label)}
                        className={`w-full rounded-lg border px-2.5 py-2 text-left transition hover:shadow ${kind.card} ${
                          selectedId === c.course_id ? "ring-2 ring-blue-500" : ""
                        }`}
                        data-testid="course-card"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-mono text-[10px] text-slate-500">{c.course_id}</span>
                          <span className="text-[10px] font-semibold text-slate-600">{c.credits} TC</span>
                        </div>
                        <div className="mt-0.5 text-xs leading-snug font-medium text-slate-800">{c.name}</div>
                        {c.badges && c.badges.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {c.badges.map((b) => (
                              <Badge key={b} text={b} />
                            ))}
                          </div>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}

export function BlockLegend() {
  return (
    <div className="flex flex-wrap gap-3 text-xs text-slate-500">
      {["general", "foundation", "major", "free", "graduation"].map((k) => (
        <span key={k} className="flex items-center gap-1.5">
          <span className={`h-2.5 w-2.5 rounded-full ${blockKind(k).dot}`} />
          {blockKind(k).label}
        </span>
      ))}
    </div>
  );
}
