import type { ReactNode } from "react";

import { BADGE_STYLE } from "../lib/format";

export function Badge({ text }: { text: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${BADGE_STYLE[text] ?? "bg-slate-100 text-slate-600"}`}>
      {text}
    </span>
  );
}

export function Spinner({ label = "Đang tính toán…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-slate-500" role="status">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      {label}
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{msg}</div>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="card p-10 text-center">
      <h2 className="text-lg font-semibold text-slate-700">{title}</h2>
      <div className="mt-2 text-sm text-slate-500">{children}</div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function Stat({ label, value, hint }: { label: string; value: ReactNode; hint?: string }) {
  return (
    <div className="card px-4 py-3">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 text-lg font-semibold text-slate-900">{value}</div>
      {hint && <div className="text-xs text-slate-400">{hint}</div>}
    </div>
  );
}
