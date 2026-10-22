import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import type { SpecializationScore } from "../api/types";
import { Empty, ErrorBox, PageHeader, Spinner } from "../components/ui";
import { useAppStore, usePayload } from "../store/useAppStore";
import { InterestEditor } from "./ProfilePage";

const COMPONENTS = [
  { key: "academic", label: "Học lực", color: "#2563eb" },
  { key: "interest", label: "Sở thích", color: "#16a34a" },
  { key: "career", label: "Nghề nghiệp", color: "#d97706" },
  { key: "progress", label: "Tiến độ", color: "#9333ea" },
] as const;

export default function AdvisorPage() {
  const navigate = useNavigate();
  const { dataset, profile, setProfile, setPrefs, setResult } = useAppStore();
  const payload = usePayload();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: api.datasets });
  const summary = datasets.data?.find((d) => d.id === dataset);
  const [weights, setWeights] = useState<Record<string, number>>({ academic: 0.35, interest: 0.3, career: 0.15, progress: 0.2 });
  const advise = useMutation({ mutationFn: () => api.advisor(payload!, weights) });
  const choose = useMutation({
    mutationFn: async (spec: string) => {
      setPrefs({ specialization: spec });
      const p = useAppStore.getState();
      return api.plans({ dataset: p.dataset, regulation: p.regulation, student: p.profile!, preferences: p.prefs });
    },
    onSuccess: (r) => {
      setResult(r);
      navigate("/plans");
    },
  });

  if (!profile || !summary)
    return (
      <Empty title="Chưa chọn sinh viên">
        Hãy vào <Link className="text-blue-700 underline" to="/">Hồ sơ & tùy chọn</Link> để chọn sinh viên.
      </Empty>
    );

  const ranking = advise.data?.ranking ?? [];
  return (
    <div>
      <PageHeader
        title="Tư vấn chọn chuyên ngành"
        subtitle="Kết hợp học lực ở các môn nền tảng, sở thích, mục tiêu nghề nghiệp và tác động đến tiến độ tốt nghiệp (do bộ tối ưu tính thử)."
        actions={
          <button className="btn-primary" onClick={() => advise.mutate()} disabled={advise.isPending} data-testid="run-advisor">
            {advise.isPending ? "Đang phân tích…" : "Phân tích"}
          </button>
        }
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <InterestEditor profile={profile} topics={summary.topics} careers={summary.careers} onChange={setProfile} />
          <div className="card space-y-3 p-5">
            <h2 className="text-sm font-semibold text-slate-800">Trọng số đánh giá</h2>
            {COMPONENTS.map((c) => (
              <div key={c.key}>
                <div className="flex justify-between text-xs text-slate-600">
                  <span>{c.label}</span>
                  <span>{Math.round(weights[c.key] * 100)}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  className="w-full"
                  value={weights[c.key]}
                  onChange={(e) => setWeights({ ...weights, [c.key]: Number(e.target.value) })}
                />
              </div>
            ))}
          </div>
        </div>
        <div className="space-y-4 lg:col-span-2">
          {advise.error && <ErrorBox error={advise.error} />}
          {advise.isPending && <Spinner label="Đang chạy thử bộ tối ưu cho từng chuyên ngành…" />}
          {!advise.data && !advise.isPending && (
            <div className="card p-8 text-center text-sm text-slate-500">Điều chỉnh sở thích rồi bấm “Phân tích”.</div>
          )}
          {advise.data && (
            <div className={`rounded-lg px-4 py-2 text-sm ${advise.data.stable ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-900"}`}>
              {advise.data.stability_note}
              {advise.data.gpa ? ` · GPA hiện tại ${advise.data.gpa}` : ""}
            </div>
          )}
          {ranking.map((r) => (
            <SpecCard key={r.specialization} r={r} weights={advise.data!.weights} onChoose={() => choose.mutate(r.specialization)} busy={choose.isPending} />
          ))}
          {choose.error && <ErrorBox error={choose.error} />}
        </div>
      </div>
    </div>
  );
}

function SpecCard({ r, weights, onChoose, busy }: { r: SpecializationScore; weights: Record<string, number>; onChoose: () => void; busy: boolean }) {
  const comp = r.components as unknown as Record<string, number>;
  return (
    <div className={`card p-5 ${r.rank === 1 ? "ring-2 ring-blue-500" : ""}`} data-testid="spec-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-semibold text-slate-400">#{r.rank}</div>
          <h3 className="text-lg font-bold text-slate-900">{r.name}</h3>
          <p className="text-sm text-slate-500">{r.description}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-700">{Math.round(r.score * 100)}</div>
          <div className="text-xs text-slate-400">điểm phù hợp · độ tin cậy {r.confidence}</div>
        </div>
      </div>
      <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-slate-100" title="Đóng góp có trọng số của từng thành phần">
        {COMPONENTS.map((c) => (
          <div key={c.key} style={{ width: `${(weights[c.key] ?? 0) * (comp[c.key] ?? 0) * 100}%`, background: c.color }} />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-600">
        {COMPONENTS.map((c) => (
          <span key={c.key} className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: c.color }} />
            {c.label}: {Math.round((comp[c.key] ?? 0) * 100)}
          </span>
        ))}
      </div>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {(r.reasons ?? []).map((x, i) => (
          <li key={i}>{x}</li>
        ))}
      </ul>
      <div className="mt-4 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {r.graduation_term ? `Tốt nghiệp sớm nhất: ${r.graduation_term}` : r.feasible ? "" : "Không khả thi trong thời gian còn lại"}
        </span>
        <button className="btn-secondary" onClick={onChoose} disabled={!r.feasible || busy}>
          Chọn & lập lộ trình
        </button>
      </div>
    </div>
  );
}
