import { create } from "zustand";

import type { PlanResult, Preferences, StudentProfile } from "../api/types";

export const DEFAULT_DATASET = "hcmus_cntt_k2020";

export const defaultPreferences = (): Preferences => ({
  summer_enabled: false,
  personal_max_credits: null,
  target_graduation_term: null,
  specialization: null,
  pinned: [],
  excluded: [],
  objective_weights: { fast: 0.25, balance: 0.35, risk: 0.25, interest: 0.15 },
  assume_in_progress_pass: true,
});

interface AppState {
  dataset: string;
  regulation: string | null;
  studentId: string | null;
  profile: StudentProfile | null;
  prefs: Preferences;
  result: PlanResult | null;
  selectedPlanId: string | null;
  setRegulation: (id: string | null) => void;
  loadStudent: (id: string, profile: StudentProfile) => void;
  setProfile: (p: StudentProfile) => void;
  setPrefs: (p: Partial<Preferences>) => void;
  setResult: (r: PlanResult | null) => void;
  selectPlan: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  dataset: DEFAULT_DATASET,
  regulation: "default",
  studentId: null,
  profile: null,
  prefs: defaultPreferences(),
  result: null,
  selectedPlanId: null,
  setRegulation: (regulation) => set({ regulation }),
  loadStudent: (id, profile) =>
    set({
      studentId: id,
      profile,
      prefs: { ...defaultPreferences(), ...(profile.preferences ?? {}) },
      result: null,
      selectedPlanId: null,
    }),
  setProfile: (profile) => set({ profile }),
  setPrefs: (p) => set((s) => ({ prefs: { ...s.prefs, ...p } })),
  setResult: (result) => set({ result, selectedPlanId: result?.plans?.[0]?.id ?? null }),
  selectPlan: (selectedPlanId) => set({ selectedPlanId }),
}));

export function usePayload() {
  const { dataset, regulation, profile, prefs } = useAppStore();
  return profile ? { dataset, regulation, student: profile, preferences: prefs } : null;
}
