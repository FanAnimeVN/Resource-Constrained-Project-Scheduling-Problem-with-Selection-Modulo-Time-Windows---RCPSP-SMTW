import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { CourseSuggestion, Strategy } from "../api/types";
import ConflictReport from "../components/ConflictReport";
import { Badge, Empty, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { useAppStore, usePayload } from "../store/useAppStore";

const STRATEGIES: { id: Strategy; label: string }[] = [
  { id: "PERSONALIZED", label: "Đề xuất cho bạn" },
  { id: "BALANCED", label: "Cân bằng tải" },
  { id: "FAST_TRACK", label: "Tốt nghiệp sớm" },
  { id: "RISK_AVERSE", label: "An toàn" },
];

export default function NextTermPage() {
  const { profile } = useAppStore();
  const payload = usePayload();
  const [strategy, setStrategy] = useState<Strategy>("PERSONALIZED");
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const q = useMutation({ mutationFn: () => api.nextTerm(payload!, strategy) });

  useEffect(() => {
    if (q.data?.advice) setPicked(new Set(q.data.advice.recommended.map((r) => r.course_id)));
  }, [q.data]);

  if (!profile)
    return (
      <Empty title="Chưa chọn sinh viên">
        Hãy vào <Link className="text-blue-700 underline" to="/">Hồ sơ & tùy chọn</Link> để chọn sinh viên.
      </Empty>
    );
  const adv = q.data?.advice;
  const all: CourseSuggestion[] = adv ? [...adv.recommended, ...adv.alternatives] : [];
  const total = all.filter((c) => picked.has(c.course_id)).reduce((s, c) => s + c.credits, 0);
  const lo = adv?.min_credits ?? 0;
  const hi = adv?.max_credits ?? 0;
  const toggle = (id: string) => setPicked((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    return n;
  });

  return (
    <div>
      <PageHeader
        title="Gợi ý đăng ký học phần kỳ tới"
        subtitle="Danh sách lấy từ học kỳ đầu tiên của phương án tối ưu; bạn có thể thay bằng môn khác đủ điều kiện."
        actions={
          <div className="flex gap-2">
            <select className="input w-auto" value={strategy} onChange={(e) => setStrategy(e.target.value as Strategy)}>
              {STRATEGIES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
            <button className="btn-primary whitespace-nowrap" onClick={() => q.mutate()} disabled={q.isPending} data-testid="run-next-term">
              Gợi ý
            </button>
          </div>
        }
      />
      {q.isPending && <Spinner />}
      {q.error && <ErrorBox error={q.error} />}
      {q.data && q.data.status === "INFEASIBLE" && q.data.plan_result.infeasibility && (
        <ConflictReport report={q.data.plan_result.infeasibility} />
      )}
      {adv && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-2">
            <div className="card p-5">
              <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-base font-semibold text-slate-800">Đăng ký {adv.term}</h2>
                <span className={`text-sm font-semibold ${total > hi || (lo && total < lo) ? "text-red-600" : "text-emerald-700"}`}>
                  Đã chọn {total} TC (giới hạn {lo ?? 0}–{hi})
                </span>
              </div>
              <SuggestionList items={adv.recommended} picked={picked} onToggle={toggle} />
            </div>
            <div className="card p-5">
              <h2 className="mb-3 text-base font-semibold text-slate-800">Môn có thể thay thế</h2>
              <SuggestionList items={adv.alternatives} picked={picked} onToggle={toggle} />
            </div>
          </div>
          <div className="card h-fit p-5">
            <h2 className="mb-2 text-sm font-semibold text-slate-800">Lưu ý</h2>
            {(adv.warnings ?? []).length === 0 ? (
              <p className="text-sm text-slate-500">Không có cảnh báo.</p>
            ) : (
              <ul className="list-disc space-y-1.5 pl-5 text-sm text-amber-900">
                {(adv.warnings ?? []).map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SuggestionList({ items, picked, onToggle }: { items: CourseSuggestion[]; picked: Set<string>; onToggle: (id: string) => void }) {
  if (!items.length) return <p className="text-sm text-slate-500">Không có môn phù hợp.</p>;
  return (
    <ul className="divide-y divide-slate-100">
      {items.map((s) => (
        <li key={s.course_id} className="flex gap-3 py-2.5">
          <input type="checkbox" className="mt-1" checked={picked.has(s.course_id)} onChange={() => onToggle(s.course_id)} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-slate-500">{s.course_id}</span>
              <span className="text-sm font-medium text-slate-800">{s.name}</span>
              <span className="text-xs text-slate-500">{s.credits} TC</span>
              {s.mandatory && <span className="rounded bg-indigo-100 px-1.5 text-[10px] font-semibold text-indigo-700">bắt buộc</span>}
              {(s.badges ?? []).map((b) => (
                <Badge key={b} text={b} />
              ))}
            </div>
            <div className="mt-0.5 text-xs text-slate-500">{(s.reasons ?? []).join(" ")}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}
