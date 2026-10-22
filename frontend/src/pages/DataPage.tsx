import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "../api/client";
import type { CurriculumResponse } from "../api/types";
import PrereqGraph, { EdgeLegend } from "../components/PrereqGraph";
import { ErrorBox, PageHeader, Spinner, Stat } from "../components/ui";
import { useAppStore } from "../store/useAppStore";

type Block = CurriculumResponse["curriculum"]["blocks"][number];

function BlockTree({ blocks, depth = 0 }: { blocks: Block[]; depth?: number }) {
  return (
    <ul className={depth ? "ml-4 border-l border-slate-200 pl-3" : ""}>
      {blocks.map((b) => (
        <li key={b.id} className="py-1">
          <div className="flex items-baseline justify-between gap-2 text-sm">
            <span className={depth ? "text-slate-700" : "font-semibold text-slate-900"}>{b.name}</span>
            <span className="text-xs whitespace-nowrap text-slate-500">
              {b.required_credits} TC · {b.rule === "ALL_MANDATORY" ? "bắt buộc" : b.rule === "PICK_K_OF_N" ? `chọn ${b.k}` : "tối thiểu"}
            </span>
          </div>
          {(b.children ?? []).length > 0 && <BlockTree blocks={b.children as Block[]} depth={depth + 1} />}
          {(b.courses ?? []).length > 0 && depth > 0 && (
            <div className="text-[11px] text-slate-400">{(b.courses ?? []).length} học phần</div>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function DataPage() {
  const { dataset } = useAppStore();
  const catalog = useQuery({ queryKey: ["courses", dataset], queryFn: () => api.courses(dataset) });
  const cur = useQuery({ queryKey: ["curriculum", dataset], queryFn: () => api.curriculum(dataset) });
  const val = useQuery({ queryKey: ["validation", dataset], queryFn: () => api.validation(dataset) });
  const [filter, setFilter] = useState("CSN+DC");
  const [focus, setFocus] = useState<string | null>(null);

  const groups = useMemo(() => {
    const out: Record<string, Set<string>> = {};
    const walk = (b: Block, root: string) => {
      for (const c of b.courses ?? []) (out[root] ??= new Set()).add(c.id);
      for (const ch of (b.children ?? []) as Block[]) walk(ch, ch.specialization ? ch.id : root);
    };
    for (const b of cur.data?.curriculum.blocks ?? []) walk(b, b.id);
    return out;
  }, [cur.data]);

  const visible = useMemo(() => {
    const s = new Set<string>();
    const add = (k: string) => groups[k]?.forEach((c) => s.add(c));
    if (filter === "ALL") Object.keys(groups).forEach(add);
    else if (filter === "CSN+DC") {
      add("CSN");
      add("DC");
    } else {
      add("CSN");
      add(filter);
    }
    return s;
  }, [groups, filter]);

  if (catalog.isLoading || cur.isLoading) return <Spinner label="Đang tải dữ liệu CTĐT…" />;
  if (catalog.error) return <ErrorBox error={catalog.error} />;
  const c = cur.data!.curriculum;
  const issues = val.data?.issues ?? [];
  const specBlocks = c.specializations ?? [];

  return (
    <div>
      <PageHeader title="Dữ liệu chương trình đào tạo" subtitle={c.name} />
      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Tổng tín chỉ" value={`${c.credit_rule === "exact" ? "=" : "≥"} ${c.total_credits_required} TC`} />
        <Stat label="Học phần" value={catalog.data!.courses.length} />
        <Stat label="Quan hệ phụ thuộc" value={catalog.data!.dependencies.length} />
        <Stat label="Kiểm tra dữ liệu" value={issues.length ? `${issues.length} vấn đề` : "Hợp lệ"} hint="DV-01..DV-14" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <div className="card p-5">
            <h2 className="mb-2 text-sm font-semibold text-slate-800">Cây khối kiến thức</h2>
            <BlockTree blocks={c.blocks as Block[]} />
          </div>
          <div className="card p-5">
            <h2 className="mb-2 text-sm font-semibold text-slate-800">Báo cáo kiểm tra dữ liệu</h2>
            {issues.length === 0 ? (
              <p className="text-sm text-emerald-700">Không phát hiện lỗi: không có chu trình, tham chiếu hợp lệ, các khối đủ tín chỉ.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {issues.map((i, k) => (
                  <li key={k}>
                    <b>{i.code}</b> {i.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        <div className="lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <select className="input max-w-xs" value={filter} onChange={(e) => { setFilter(e.target.value); setFocus(null); }}>
              <option value="CSN+DC">Đại cương + Cơ sở ngành</option>
              {specBlocks.map((s) => (
                <option key={s.id} value={s.block_id}>
                  Cơ sở ngành + {s.name}
                </option>
              ))}
              <option value="ALL">Toàn bộ</option>
            </select>
            <EdgeLegend />
          </div>
          <PrereqGraph catalog={catalog.data!} visible={visible} focus={focus} onFocus={setFocus} />
          <p className="mt-2 text-xs text-slate-400">Bấm một môn để tô sáng toàn bộ chuỗi điều kiện phía trước nó.</p>
        </div>
      </div>
    </div>
  );
}
