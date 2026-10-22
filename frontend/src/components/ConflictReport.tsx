import type { InfeasibilityReport } from "../api/types";

export default function ConflictReport({ report }: { report: InfeasibilityReport }) {
  return (
    <div className="space-y-4" data-testid="conflict-report">
      <div className="rounded-xl border border-red-200 bg-red-50 p-5">
        <h2 className="text-lg font-bold text-red-800">Không có lộ trình hợp lệ</h2>
        <p className="mt-1 text-sm text-red-700">{report.summary}</p>
      </div>
      {(report.prechecks ?? []).length > 0 && (
        <div className="card p-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-800">Chẩn đoán nhanh</h3>
          <ul className="space-y-2">
            {(report.prechecks ?? []).map((p, i) => (
              <li key={i} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                <span className="mr-2 rounded bg-red-100 px-1.5 py-0.5 font-mono text-[11px] text-red-700">{p.code}</span>
                {p.message}
              </li>
            ))}
          </ul>
        </div>
      )}
      {(report.conflicts ?? []).length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-800">
            Tập luật xung đột {report.minimal ? "tối thiểu" : "(chưa chắc tối thiểu)"}
          </h3>
          <p className="mb-3 text-xs text-slate-500">Các luật dưới đây không thể đồng thời thỏa mãn; bỏ bất kỳ luật nào sẽ có lời giải.</p>
          <ul className="space-y-1.5">
            {(report.conflicts ?? []).map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className={`mt-0.5 rounded px-1.5 py-0.5 font-mono text-[11px] ${c.relaxable ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"}`}>
                  {c.code}
                </span>
                <span>{c.message}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {(report.suggestions ?? []).length > 0 && (
        <div className="card p-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-800">Gợi ý tháo gỡ</h3>
          <ul className="list-disc space-y-1 pl-5 text-sm text-emerald-800">
            {(report.suggestions ?? []).map((s, i) => (
              <li key={i}>{s.message}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
