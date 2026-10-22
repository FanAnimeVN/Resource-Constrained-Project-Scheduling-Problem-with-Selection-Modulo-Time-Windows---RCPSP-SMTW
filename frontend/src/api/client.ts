import type {
  CatalogResponse,
  CurriculumResponse,
  DatasetSummary,
  NextTermResponse,
  Plan,
  PlanResult,
  Preferences,
  SpecializationAdvice,
  Strategy,
  StudentProfile,
  ValidationReport,
  WhatIfResult,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const text = await res.text();
  const body = text ? JSON.parse(text) : undefined;
  if (!res.ok && res.status !== 422) {
    const detail = (body as { detail?: unknown })?.detail;
    throw new ApiError(res.status, typeof detail === "string" ? detail : `Lỗi máy chủ (${res.status})`, body);
  }
  return body as T;
}

const post = <T>(path: string, data: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(data) });

export interface StudentPayload {
  dataset: string;
  regulation?: string | null;
  student: StudentProfile;
  preferences: Preferences;
}

export const api = {
  datasets: () => request<DatasetSummary[]>("/api/datasets"),
  curriculum: (ds: string) => request<CurriculumResponse>(`/api/datasets/${ds}/curriculum`),
  courses: (ds: string) => request<CatalogResponse>(`/api/datasets/${ds}/courses`),
  validation: (ds: string) => request<ValidationReport>(`/api/datasets/${ds}/validation`),
  student: (ds: string, id: string) => request<StudentProfile>(`/api/datasets/${ds}/students/${id}`),
  plans: (p: StudentPayload, strategies?: Strategy[]) =>
    post<PlanResult>("/api/plans", { ...p, strategies: strategies ?? null, explain: true }),
  advisor: (p: StudentPayload, weights: Record<string, number>) =>
    post<SpecializationAdvice>("/api/advisor/specializations", { ...p, weights }),
  nextTerm: (p: StudentPayload, strategy: Strategy) =>
    post<NextTermResponse>("/api/recommendations/next-term", { ...p, strategy }),
  whatIf: (p: StudentPayload, plan: Plan, courseId: string) =>
    post<WhatIfResult>("/api/what-if/fail", { ...p, plan, course_id: courseId }),
};
