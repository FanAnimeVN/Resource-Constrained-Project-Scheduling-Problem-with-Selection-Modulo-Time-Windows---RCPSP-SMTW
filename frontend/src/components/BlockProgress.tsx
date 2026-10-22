import type { Plan } from "../api/types";

export default function BlockProgress({ plan }: { plan: Plan }) {
  const rows = (plan.block_progress ?? []).filter((b) => b.depth <= 1 && b.required > 0);
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-800">Tiến độ theo khối kiến thức</h3>
      <div className="space-y-2.5">
        {rows.map((b) => {
          const total = b.passed_credits + b.planned_credits;
          const passedW = Math.min(100, (b.passed_credits / b.required) * 100);
          const plannedW = Math.min(100 - passedW, (b.planned_credits / b.required) * 100);
          return (
            <div key={b.block_id} className={b.depth ? "pl-4" : ""}>
              <div className="flex justify-between text-xs">
                <span className={b.depth ? "text-slate-600" : "font-semibold text-slate-800"}>{b.name}</span>
                <span className="text-slate-500">
                  {total}/{b.required} TC
                </span>
              </div>
              <div className="mt-1 flex h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="bg-emerald-500" style={{ width: `${passedW}%` }} title={`Đã đạt ${b.passed_credits} TC`} />
                <div className="bg-blue-400" style={{ width: `${plannedW}%` }} title={`Dự kiến ${b.planned_credits} TC`} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 flex gap-4 text-[11px] text-slate-500">
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500" />Đã đạt</span>
        <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-400" />Trong lộ trình</span>
      </div>
    </div>
  );
}
