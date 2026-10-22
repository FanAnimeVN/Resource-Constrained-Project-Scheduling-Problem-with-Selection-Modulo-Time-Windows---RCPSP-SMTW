import { Link } from "react-router-dom";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Empty, PageHeader } from "../components/ui";
import { STRATEGY_COLOR, pct } from "../lib/format";
import { useAppStore } from "../store/useAppStore";

export default function ComparePage() {
  const { result } = useAppStore();
  const plans = result?.plans ?? [];
  if (!plans.length)
    return (
      <Empty title="Chưa có phương án để so sánh">
        Hãy <Link className="text-blue-700 underline" to="/">lập lộ trình</Link> trước.
      </Empty>
    );

  const labels: string[] = [];
  for (const p of plans) for (const t of p.terms) if (!labels.includes(t.label)) labels.push(t.label);
  const order = (l: string) => {
    const [kind, years] = l.split(" ");
    const y = parseInt(years, 10);
    return kind === "Hè" ? (y - 1) * 3 + 2 : y * 3 + (kind === "HK1" ? 0 : 1);
  };
  labels.sort((a, b) => order(a) - order(b));
  const data = labels.map((label) => {
    const row: Record<string, string | number | null> = { label };
    for (const p of plans) row[p.id] = p.terms.find((t) => t.label === label)?.credits ?? null;
    return row;
  });

  const rows: { label: string; get: (m: (typeof plans)[number]["metrics"]) => string | number; best?: "min" | "max"; raw?: (m: (typeof plans)[number]["metrics"]) => number }[] = [
    { label: "Kỳ tốt nghiệp", get: (m) => m.graduation_term, best: "min", raw: (m) => m.graduation_index },
    { label: "Số kỳ chính còn lại", get: (m) => m.main_terms_remaining, best: "min", raw: (m) => m.main_terms_remaining },
    { label: "Tín chỉ phải học thêm", get: (m) => m.planned_credits, best: "min", raw: (m) => m.planned_credits },
    { label: "Độ lệch chuẩn tải (TC)", get: (m) => m.load_std, best: "min", raw: (m) => m.load_std },
    { label: "Tải cao nhất (TC)", get: (m) => m.load_max, best: "min", raw: (m) => m.load_max },
    { label: "Độ nặng kỳ nặng nhất", get: (m) => m.peak_workload, best: "min", raw: (m) => m.peak_workload },
    { label: "Số kỳ hè", get: (m) => m.summers_used, best: "min", raw: (m) => m.summers_used },
    { label: "Đệm học lại (môn bắt buộc)", get: (m) => pct(m.risk_coverage), best: "max", raw: (m) => m.risk_coverage },
    { label: "Khớp sở thích", get: (m) => pct(m.interest_score), best: "max", raw: (m) => m.interest_score },
    { label: "Trạng thái lời giải", get: (m) => (m.solver_status === "OPTIMAL" ? "Tối ưu" : "Gần tối ưu") },
  ];

  return (
    <div>
      <PageHeader title="So sánh các phương án" subtitle="Ô tô đậm là giá trị tốt nhất của mỗi chỉ số." />
      <div className="card mb-6 overflow-x-auto">
        <table className="w-full text-sm" data-testid="metrics-table">
          <thead>
            <tr className="border-b border-slate-200 text-left">
              <th className="px-4 py-3 text-xs text-slate-500">Chỉ số</th>
              {plans.map((p) => (
                <th key={p.id} className="px-4 py-3 text-xs font-semibold" style={{ color: STRATEGY_COLOR[p.strategy] }}>
                  {p.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const vals = r.raw ? plans.map((p) => r.raw!(p.metrics)) : [];
              const best = r.best === "min" ? Math.min(...vals) : Math.max(...vals);
              return (
                <tr key={r.label} className="border-b border-slate-100">
                  <td className="px-4 py-2 text-slate-600">{r.label}</td>
                  {plans.map((p, i) => (
                    <td key={p.id} className={`px-4 py-2 ${r.raw && vals[i] === best ? "font-bold text-slate-900" : "text-slate-700"}`}>
                      {r.get(p.metrics)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="card mb-6 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Số tín chỉ theo học kỳ</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ left: -10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {plans.map((p) => (
                <Line key={p.id} type="linear" dot={{ r: 3 }} dataKey={p.id} name={p.title} stroke={STRATEGY_COLOR[p.strategy]} strokeWidth={2} connectNulls={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {result?.comparison && (
        <div className="card overflow-x-auto p-4">
          <h3 className="mb-1 text-sm font-semibold text-slate-800">Khoảng cách giữa các phương án</h3>
          <p className="mb-3 text-xs text-slate-500">= số môn khác kỳ + số môn khác nhau + chênh kỳ tốt nghiệp. Càng lớn càng khác biệt.</p>
          <table className="text-sm">
            <thead>
              <tr>
                <th />
                {plans.map((p) => (
                  <th key={p.id} className="px-3 py-1 text-xs" style={{ color: STRATEGY_COLOR[p.strategy] }}>
                    {p.title}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {plans.map((a) => (
                <tr key={a.id}>
                  <td className="pr-3 text-xs font-semibold" style={{ color: STRATEGY_COLOR[a.strategy] }}>
                    {a.title}
                  </td>
                  {plans.map((b) => (
                    <td key={b.id} className="px-3 py-1 text-center text-slate-700">
                      {a.id === b.id ? "–" : result.comparison!.distances[a.id]?.[b.id]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
