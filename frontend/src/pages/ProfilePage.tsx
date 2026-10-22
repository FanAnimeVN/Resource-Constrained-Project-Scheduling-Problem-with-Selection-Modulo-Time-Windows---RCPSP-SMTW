import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import type { AcademicRecord, StudentProfile } from "../api/types";
import { ErrorBox, PageHeader, Spinner } from "../components/ui";
import { STATUS_LABEL, nextTerms, termLabel } from "../lib/format";
import { useAppStore, usePayload } from "../store/useAppStore";

const WEIGHT_LABELS: Record<string, string> = {
  fast: "Tốt nghiệp sớm",
  balance: "Cân bằng tải",
  risk: "An toàn trước rủi ro",
  interest: "Theo sở thích",
};

export default function ProfilePage() {
  const navigate = useNavigate();
  const { dataset, regulation, studentId, profile, prefs, setRegulation, loadStudent, setProfile, setPrefs, setResult } =
    useAppStore();
  const payload = usePayload();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: api.datasets });
  const catalog = useQuery({ queryKey: ["courses", dataset], queryFn: () => api.courses(dataset) });
  const summary = datasets.data?.find((d) => d.id === dataset);

  const pick = useMutation({
    mutationFn: (id: string) => api.student(dataset, id),
    onSuccess: (p, id) => loadStudent(id, p),
  });
  const run = useMutation({
    mutationFn: () => api.plans(payload!),
    onSuccess: (r) => {
      setResult(r);
      navigate("/plans");
    },
  });

  if (datasets.isLoading) return <Spinner label="Đang tải dữ liệu…" />;
  if (datasets.error) return <ErrorBox error={datasets.error} />;

  return (
    <div>
      <PageHeader
        title="Hồ sơ sinh viên & tùy chọn"
        subtitle="Chọn một sinh viên mẫu hoặc chỉnh hồ sơ, đặt mong muốn của bạn rồi bấm “Lập lộ trình”."
        actions={
          <button className="btn-primary" disabled={!profile || run.isPending} onClick={() => run.mutate()} data-testid="run-plan">
            {run.isPending ? "Đang tối ưu…" : "Lập lộ trình"}
          </button>
        }
      />
      {run.error && <ErrorBox error={run.error} />}
      {run.isPending && <Spinner label="Đang giải bài toán tối ưu (CP-SAT) cho 5 chiến lược…" />}

      <div className="card mb-6 p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-800">1. Chọn sinh viên mẫu</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {summary?.students.map((s) => (
            <button
              key={s.id}
              onClick={() => pick.mutate(s.id)}
              className={`rounded-lg border p-3 text-left text-sm transition hover:border-blue-400 ${
                studentId === s.id ? "border-blue-600 bg-blue-50" : "border-slate-200 bg-white"
              }`}
              data-testid={`student-${s.id}`}
            >
              <div className="font-semibold text-slate-800">{s.name}</div>
              <div className="mt-0.5 text-xs text-slate-500">Kỳ tiếp theo: {s.next_term}</div>
              <div className="mt-1 text-xs text-slate-600">{s.note}</div>
            </button>
          ))}
        </div>
        <div className="mt-4 max-w-sm">
          <label className="label" htmlFor="reg">Bộ quy chế</label>
          <select id="reg" className="input" value={regulation ?? ""} onChange={(e) => setRegulation(e.target.value || null)}>
            {summary?.regulations.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.min_credits_main}–{r.max_credits_main} TC/kỳ)
              </option>
            ))}
          </select>
        </div>
      </div>

      {pick.isPending && <Spinner label="Đang tải hồ sơ…" />}
      {profile && summary && (
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-3">
            <ProfileCard profile={profile} onChange={setProfile} />
            <RecordsEditor
              profile={profile}
              onChange={setProfile}
              courses={catalog.data?.courses.map((c) => c.course) ?? []}
            />
            <InterestEditor
              profile={profile}
              topics={summary.topics}
              careers={summary.careers}
              onChange={setProfile}
              title="5. Sở thích & mục tiêu nghề nghiệp"
            />
          </div>
          <div className="space-y-6 lg:col-span-2">
            <div className="card space-y-4 p-5">
              <h2 className="text-sm font-semibold text-slate-800">3. Mong muốn của bạn</h2>
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={prefs.summer_enabled ?? false}
                  onChange={(e) => setPrefs({ summer_enabled: e.target.checked })}
                />
                Đăng ký học kỳ hè
              </label>
              <div>
                <label className="label" htmlFor="spec">Chuyên ngành</label>
                <select
                  id="spec"
                  className="input"
                  value={prefs.specialization ?? ""}
                  onChange={(e) => setPrefs({ specialization: e.target.value || null })}
                >
                  <option value="">{profile.declared_specialization ? "Theo chuyên ngành đã đăng ký" : "Để hệ thống gợi ý"}</option>
                  {summary.specializations.map((s) => (
                    <option key={String(s.id)} value={String(s.id)}>
                      {String(s.name)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label" htmlFor="maxc">Tối đa TC/kỳ (riêng)</label>
                  <input
                    id="maxc"
                    type="number"
                    min={0}
                    className="input"
                    value={prefs.personal_max_credits ?? ""}
                    placeholder="Theo quy chế"
                    onChange={(e) => setPrefs({ personal_max_credits: e.target.value ? Number(e.target.value) : null })}
                  />
                </div>
                <div>
                  <label className="label" htmlFor="target">Tốt nghiệp chậm nhất</label>
                  <select
                    id="target"
                    className="input"
                    value={prefs.target_graduation_term ? termLabel(prefs.target_graduation_term) : ""}
                    onChange={(e) => {
                      const t = nextTerms(profile.next_term, 16).find((x) => termLabel(x) === e.target.value);
                      setPrefs({ target_graduation_term: t ?? null });
                    }}
                  >
                    <option value="">Không đặt</option>
                    {nextTerms(profile.next_term, 16)
                      .filter((t) => t.kind !== "HE")
                      .map((t) => (
                        <option key={termLabel(t)}>{termLabel(t)}</option>
                      ))}
                  </select>
                </div>
              </div>
              <ExcludePicker
                excluded={prefs.excluded ?? []}
                courses={catalog.data?.courses.map((c) => c.course) ?? []}
                onChange={(excluded) => setPrefs({ excluded })}
              />
            </div>
            <div className="card space-y-3 p-5">
              <h2 className="text-sm font-semibold text-slate-800">4. Ưu tiên cho phương án “Đề xuất cho bạn”</h2>
              {Object.entries(WEIGHT_LABELS).map(([k, label]) => {
                const w = prefs.objective_weights as Record<string, number>;
                return (
                  <div key={k}>
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>{label}</span>
                      <span>{Math.round((w?.[k] ?? 0) * 100)}</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={w?.[k] ?? 0}
                      className="w-full"
                      onChange={(e) =>
                        setPrefs({ objective_weights: { ...prefs.objective_weights, [k]: Number(e.target.value) } as never })
                      }
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileCard({ profile, onChange }: { profile: StudentProfile; onChange: (p: StudentProfile) => void }) {
  const options = nextTerms({ year: profile.cohort_year, kind: "HK1" }, 18, true);
  return (
    <div className="card p-5">
      <h2 className="mb-3 text-sm font-semibold text-slate-800">2. Thông tin học tập</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        <div>
          <label className="label">Họ tên</label>
          <div className="text-sm font-medium">{profile.name}</div>
        </div>
        <div>
          <label className="label">Khóa</label>
          <div className="text-sm font-medium">{profile.cohort_year}</div>
        </div>
        <div>
          <label className="label" htmlFor="nt">Kỳ cần lập kế hoạch</label>
          <select
            id="nt"
            className="input"
            value={termLabel(profile.next_term)}
            onChange={(e) => {
              const t = options.find((x) => termLabel(x) === e.target.value);
              if (t) onChange({ ...profile, next_term: t });
            }}
          >
            {options.map((t) => (
              <option key={termLabel(t)}>{termLabel(t)}</option>
            ))}
          </select>
        </div>
      </div>
      <label className="mt-3 flex items-center gap-3 text-sm">
        <input
          type="checkbox"
          checked={profile.academic_warning ?? false}
          onChange={(e) => onChange({ ...profile, academic_warning: e.target.checked })}
        />
        Đang bị cảnh báo học tập (áp dụng giới hạn tín chỉ riêng của quy chế)
      </label>
    </div>
  );
}

function RecordsEditor({
  profile,
  onChange,
  courses,
}: {
  profile: StudentProfile;
  onChange: (p: StudentProfile) => void;
  courses: { id: string; name: string; credits: number }[];
}) {
  const [adding, setAdding] = useState("");
  const records = profile.records ?? [];
  const byId = useMemo(() => Object.fromEntries(courses.map((c) => [c.id, c])), [courses]);
  const update = (i: number, r: Partial<AcademicRecord>) =>
    onChange({ ...profile, records: records.map((x, j) => (j === i ? { ...x, ...r } : x)) });
  const remove = (i: number) => onChange({ ...profile, records: records.filter((_, j) => j !== i) });
  const add = () => {
    const id = adding.split(" ")[0];
    if (!id) return;
    onChange({ ...profile, records: [...records, { course: id, status: "PASSED", grade: 7, term: null }] });
    setAdding("");
  };
  const passed = records
    .filter((r) => r.status === "PASSED" || r.status === "EXEMPTED")
    .reduce((s, r) => s + (byId[r.course]?.credits ?? 0), 0);
  return (
    <div className="card p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-slate-800">Kết quả học tập ({records.length} môn)</h2>
        <span className="text-xs text-slate-500">Đã đạt ~{passed} TC</span>
      </div>
      <div className="max-h-80 overflow-y-auto rounded-lg border border-slate-200">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-xs text-slate-500">
            <tr>
              <th className="px-3 py-2">Môn</th>
              <th className="px-3 py-2">Trạng thái</th>
              <th className="px-3 py-2">Điểm</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {records.length === 0 && (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-slate-400">
                  Chưa có môn nào (tân sinh viên).
                </td>
              </tr>
            )}
            {records.map((r, i) => (
              <tr key={`${r.course}-${i}`} className="border-t border-slate-100">
                <td className="px-3 py-1.5">
                  <div className="font-mono text-[11px] text-slate-500">{r.course}</div>
                  <div className="text-xs">{byId[r.course]?.name ?? "(mã cũ / ngoài danh mục)"}</div>
                </td>
                <td className="px-3 py-1.5">
                  <select className="input py-1" value={r.status} onChange={(e) => update(i, { status: e.target.value as AcademicRecord["status"] })}>
                    {Object.entries(STATUS_LABEL).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="w-20 px-3 py-1.5">
                  <input
                    type="number"
                    min={0}
                    max={10}
                    step={0.1}
                    className="input py-1"
                    value={r.grade ?? ""}
                    onChange={(e) => update(i, { grade: e.target.value === "" ? null : Number(e.target.value) })}
                  />
                </td>
                <td className="px-2">
                  <button className="text-slate-400 hover:text-red-600" onClick={() => remove(i)} aria-label="Xóa">
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="input"
          list="course-list"
          placeholder="Thêm môn đã học: gõ mã hoặc tên…"
          value={adding}
          onChange={(e) => setAdding(e.target.value)}
        />
        <datalist id="course-list">
          {courses.map((c) => (
            <option key={c.id} value={`${c.id} – ${c.name}`} />
          ))}
        </datalist>
        <button className="btn-secondary" onClick={add}>
          Thêm
        </button>
      </div>
    </div>
  );
}

function ExcludePicker({
  excluded,
  courses,
  onChange,
}: {
  excluded: string[];
  courses: { id: string; name: string }[];
  onChange: (x: string[]) => void;
}) {
  const [value, setValue] = useState("");
  return (
    <div>
      <label className="label">Môn không muốn học</label>
      <div className="mb-2 flex flex-wrap gap-1">
        {excluded.map((id) => (
          <span key={id} className="flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs">
            {id}
            <button onClick={() => onChange(excluded.filter((x) => x !== id))} aria-label={`Bỏ ${id}`}>
              ✕
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input" list="course-list-ex" value={value} onChange={(e) => setValue(e.target.value)} placeholder="Mã môn tự chọn…" />
        <datalist id="course-list-ex">
          {courses.map((c) => (
            <option key={c.id} value={`${c.id} – ${c.name}`} />
          ))}
        </datalist>
        <button
          className="btn-secondary"
          onClick={() => {
            const id = value.split(" ")[0];
            if (id && !excluded.includes(id)) onChange([...excluded, id]);
            setValue("");
          }}
        >
          Loại
        </button>
      </div>
    </div>
  );
}

export function InterestEditor({
  profile,
  topics,
  careers,
  onChange,
  title = "Sở thích & mục tiêu nghề nghiệp",
}: {
  profile: StudentProfile;
  topics: Record<string, string>;
  careers: Record<string, string>;
  onChange: (p: StudentProfile) => void;
  title?: string;
}) {
  const interests = profile.interests ?? {};
  const goals = profile.career_goals ?? [];
  return (
    <div className="card space-y-3 p-5">
      <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      {Object.entries(topics).map(([k, label]) => (
        <div key={k}>
          <div className="flex justify-between text-xs text-slate-600">
            <span>{label}</span>
            <span>{interests[k] ?? 1}/5</span>
          </div>
          <input
            type="range"
            min={1}
            max={5}
            value={interests[k] ?? 1}
            className="w-full"
            onChange={(e) => onChange({ ...profile, interests: { ...interests, [k]: Number(e.target.value) } })}
          />
        </div>
      ))}
      <div>
        <label className="label">Mục tiêu nghề nghiệp</label>
        <div className="flex flex-wrap gap-2">
          {Object.entries(careers).map(([k, label]) => {
            const on = goals.includes(k);
            return (
              <button
                key={k}
                onClick={() => onChange({ ...profile, career_goals: on ? goals.filter((g) => g !== k) : [...goals, k] })}
                className={`rounded-full border px-3 py-1 text-xs ${on ? "border-blue-600 bg-blue-50 text-blue-800" : "border-slate-300 text-slate-600"}`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
