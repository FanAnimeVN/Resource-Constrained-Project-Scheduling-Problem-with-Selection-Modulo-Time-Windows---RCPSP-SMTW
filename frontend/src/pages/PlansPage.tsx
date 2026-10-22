import { useState } from "react";
import { Link } from "react-router-dom";

import type { ScheduledCourse } from "../api/types";
import BlockProgress from "../components/BlockProgress";
import ConflictReport from "../components/ConflictReport";
import ExplanationDrawer from "../components/ExplanationDrawer";
import TermGrid, { BlockLegend } from "../components/TermGrid";
import { Empty, PageHeader, Stat } from "../components/ui";
import { STRATEGY_COLOR, STRATEGY_HINT, pct } from "../lib/format";
import { useAppStore } from "../store/useAppStore";

const SOURCE: Record<string, string> = {
  declared: "đã đăng ký",
  preference: "bạn chọn",
  advisor: "hệ thống gợi ý",
  default: "mặc định",
};

export default function PlansPage() {
  const { result, selectedPlanId, selectPlan } = useAppStore();
  const [selected, setSelected] = useState<{ course: ScheduledCourse; term: string } | null>(null);

  if (!result)
    return (
      <Empty title="Chưa có lộ trình">
        Hãy vào <Link className="text-blue-700 underline" to="/">Hồ sơ & tùy chọn</Link> để chọn sinh viên và lập lộ trình.
      </Empty>
    );

  if (result.status === "INFEASIBLE" && result.infeasibility)
    return (
      <div>
        <PageHeader title="Chẩn đoán lộ trình" subtitle="Hệ thống không đưa ra lộ trình vi phạm quy chế." />
        <ConflictReport report={result.infeasibility} />
      </div>
    );
  if (result.status !== "OK")
    return (
      <Empty title={result.status === "COMPLETED" ? "Đã đủ điều kiện tín chỉ" : "Không thể lập lộ trình"}>
        {(result.warnings ?? []).join(" ")}
      </Empty>
    );

  const plans = result.plans ?? [];
  const plan = plans.find((p) => p.id === selectedPlanId) ?? plans[0];
  const m = plan.metrics;
  return (
    <div>
      <PageHeader
        title="Lộ trình đề xuất"
        subtitle={
          <>
            Chuyên ngành: <b>{result.specialization_name}</b> ({SOURCE[result.specialization_source ?? ""] ?? ""}) · Đã tích lũy{" "}
            {result.passed_credits} TC{result.gpa ? ` · GPA ${result.gpa}` : ""}
          </>
        }
      />
      {(result.warnings ?? []).map((w, i) => (
        <div key={i} className="mb-3 rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-900">
          {w}
        </div>
      ))}
      <div className="mb-4 flex flex-wrap gap-2" role="tablist">
        {plans.map((p) => (
          <button
            key={p.id}
            role="tab"
            aria-selected={p.id === plan.id}
            onClick={() => selectPlan(p.id)}
            className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
              p.id === plan.id ? "border-transparent text-white shadow" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
            }`}
            style={p.id === plan.id ? { background: STRATEGY_COLOR[p.strategy] } : undefined}
            data-testid="plan-tab"
          >
            <div className="font-semibold">{p.title}</div>
            <div className={`text-xs ${p.id === plan.id ? "text-white/80" : "text-slate-500"}`}>
              Tốt nghiệp {p.metrics.graduation_term}
              {p.duplicate_of ? " · trùng phương án khác" : ""}
            </div>
          </button>
        ))}
      </div>
      <p className="mb-4 text-sm text-slate-500">{STRATEGY_HINT[plan.strategy]}</p>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-5">
        <Stat label="Tốt nghiệp dự kiến" value={m.graduation_term} hint={`${m.main_terms_remaining} kỳ chính nữa`} />
        <Stat label="Tổng tín chỉ" value={`${m.total_credits} TC`} hint={m.surplus_credits ? `dư ${m.surplus_credits} TC` : "đúng yêu cầu"} />
        <Stat label="Tải mỗi kỳ chính" value={`${m.load_min}–${m.load_max} TC`} hint={`độ lệch chuẩn ${m.load_std}`} />
        <Stat label="Đệm học lại" value={pct(m.risk_coverage)} hint="trọng số rủi ro môn bắt buộc" />
        <Stat label="Khớp sở thích" value={pct(m.interest_score)} hint={`lời giải ${m.solver_status === "OPTIMAL" ? "tối ưu" : "gần tối ưu"}`} />
      </div>

      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-slate-800">Kế hoạch theo học kỳ</h2>
        <BlockLegend />
      </div>
      <TermGrid plan={plan} selectedId={selected?.course.course_id} onSelect={(course, term) => setSelected({ course, term })} />
      <p className="mt-2 text-xs text-slate-400">Bấm vào một môn để xem vì sao được chọn, vì sao xếp ở kỳ đó và mô phỏng nếu rớt.</p>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card p-4">
          <h3 className="mb-2 text-sm font-semibold text-slate-800">Điểm nổi bật</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
            {(plan.highlights ?? []).map((h, i) => (
              <li key={i}>{h}</li>
            ))}
          </ul>
          {(result.graduation_conditions ?? []).length > 0 && (
            <>
              <h3 className="mt-4 mb-2 text-sm font-semibold text-slate-800">Điều kiện tốt nghiệp khác (không tính vào 138 TC)</h3>
              <ul className="space-y-1 text-sm text-slate-600">
                {(result.graduation_conditions ?? []).map((g, i) => (
                  <li key={i}>☐ {g}</li>
                ))}
              </ul>
            </>
          )}
        </div>
        <BlockProgress plan={plan} />
      </div>

      {selected && (
        <ExplanationDrawer plan={plan} course={selected.course} termLabel={selected.term} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
