import { useMutation } from "@tanstack/react-query";

import { api } from "../api/client";
import type { Plan, ScheduledCourse } from "../api/types";
import { blockKind } from "../lib/format";
import { usePayload } from "../store/useAppStore";
import { Badge, ErrorBox } from "./ui";

const SELECTION_TITLE: Record<string, string> = {
  MANDATORY: "Môn bắt buộc",
  ELECTIVE: "Môn tự chọn",
  REQUIRED_AS_PREREQ: "Môn điều kiện",
  OTHER: "Môn khác",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border-t border-slate-100 py-3">
      <h4 className="mb-1.5 text-xs font-semibold tracking-wide text-slate-500 uppercase">{title}</h4>
      {children}
    </section>
  );
}

export default function ExplanationDrawer({
  plan,
  course,
  termLabel,
  onClose,
}: {
  plan: Plan;
  course: ScheduledCourse;
  termLabel: string;
  onClose: () => void;
}) {
  const payload = usePayload();
  const e = course.explanation;
  const whatIf = useMutation({
    mutationFn: () => api.whatIf(payload!, plan, course.course_id),
  });
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-900/30" onClick={onClose}>
      <aside
        className="h-full w-full max-w-md overflow-y-auto bg-white p-5 shadow-xl"
        onClick={(ev) => ev.stopPropagation()}
        data-testid="explanation-drawer"
        aria-label="Giải trình môn học"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="font-mono text-xs text-slate-500">{course.course_id}</div>
            <h3 className="text-lg leading-snug font-bold text-slate-900">{course.name}</h3>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <span className={`h-2 w-2 rounded-full ${blockKind(course.block_kind).dot}`} />
                {blockKind(course.block_kind).label}
              </span>
              <span>· {course.credits} TC</span>
              <span>· Xếp ở {termLabel}</span>
            </div>
            {course.badges && course.badges.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {course.badges.map((b) => (
                  <Badge key={b} text={b} />
                ))}
              </div>
            )}
          </div>
          <button className="btn-secondary px-2 py-1" onClick={onClose} aria-label="Đóng">
            ✕
          </button>
        </div>

        {e && (
          <>
            <Section title={`Vì sao chọn · ${SELECTION_TITLE[e.selection_kind] ?? ""}`}>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {(e.selection ?? []).map((r, i) => (
                  <li key={i}>{r.message}</li>
                ))}
              </ul>
            </Section>
            <Section title="Vì sao xếp ở kỳ này">
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                {(e.timing ?? []).map((r, i) => (
                  <li key={i}>
                    <span className="mr-1 rounded bg-slate-100 px-1 font-mono text-[10px] text-slate-500">{r.code}</span>
                    {r.message}
                  </li>
                ))}
              </ul>
              {e.earliest_term && <p className="mt-1 text-xs text-slate-400">Sớm nhất có thể trong lộ trình này: {e.earliest_term}</p>}
            </Section>
            <Section title="Điều kiện & phụ thuộc">
              {(e.requires ?? []).length === 0 ? (
                <p className="text-sm text-slate-500">Không có môn điều kiện.</p>
              ) : (
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {(e.requires ?? []).map((r, i) => (
                    <li key={i}>{r.message}</li>
                  ))}
                </ul>
              )}
              {(e.unlocks ?? []).length > 0 && (
                <p className="mt-2 text-sm text-slate-600">
                  Mở khóa: <span className="font-mono text-xs">{(e.unlocks ?? []).join(", ")}</span>
                </p>
              )}
              {e.on_critical_path && <p className="mt-1 text-sm font-medium text-red-700">Môn nằm trên chuỗi găng: chậm môn này sẽ chậm tốt nghiệp.</p>}
            </Section>
            <Section title={`Rủi ro · ${e.risk_score}/20`}>
              <div className="mb-2 h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-purple-500" style={{ width: `${(e.risk_score / 20) * 100}%` }} />
              </div>
              {(e.risk_factors ?? []).length > 0 && (
                <ul className="list-disc space-y-0.5 pl-5 text-sm text-slate-700">
                  {(e.risk_factors ?? []).map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              )}
              {e.retake_safe !== null && e.retake_safe !== undefined && (
                <p className={`mt-2 text-sm ${e.retake_safe ? "text-emerald-700" : "text-amber-700"}`}>
                  {e.retake_safe
                    ? `Nếu không đạt, có thể học lại ở ${e.retake_term} mà vẫn kịp mục tiêu tốt nghiệp.`
                    : "Nếu không đạt, việc học lại có thể làm chậm tốt nghiệp."}
                </p>
              )}
            </Section>
          </>
        )}

        <section className="border-t border-slate-100 pt-3">
          <button className="btn-secondary w-full" disabled={!payload || whatIf.isPending} onClick={() => whatIf.mutate()}>
            {whatIf.isPending ? "Đang mô phỏng…" : "Mô phỏng: nếu rớt môn này?"}
          </button>
          {whatIf.error && <div className="mt-2"><ErrorBox error={whatIf.error} /></div>}
          {whatIf.data && (
            <div
              className={`mt-3 rounded-lg p-3 text-sm ${
                whatIf.data.delay_main_terms ? "bg-amber-50 text-amber-900" : whatIf.data.status === "OK" ? "bg-emerald-50 text-emerald-900" : "bg-red-50 text-red-800"
              }`}
              data-testid="what-if-result"
            >
              {whatIf.data.message}
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
