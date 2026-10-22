import { NavLink, Outlet } from "react-router-dom";

import { useAppStore } from "../store/useAppStore";

const NAV = [
  { to: "/", label: "Hồ sơ & tùy chọn", icon: "👤" },
  { to: "/plans", label: "Lộ trình đề xuất", icon: "🗺️" },
  { to: "/compare", label: "So sánh phương án", icon: "📊" },
  { to: "/advisor", label: "Tư vấn chuyên ngành", icon: "🧭" },
  { to: "/next-term", label: "Đăng ký kỳ tới", icon: "📝" },
  { to: "/data", label: "Dữ liệu CTĐT", icon: "🗂️" },
];

export default function Layout() {
  const { profile, result } = useAppStore();
  return (
    <div className="flex min-h-full">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white md:block">
        <div className="border-b border-slate-200 px-5 py-5">
          <div className="text-xs font-semibold tracking-widest text-blue-700 uppercase">ĐH KHTN · Khoa CNTT</div>
          <div className="mt-1 text-lg leading-tight font-bold text-slate-900">Lộ trình học tập cá nhân hóa</div>
        </div>
        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-blue-50 text-blue-800" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              <span aria-hidden>{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        {profile && (
          <div className="m-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
            <div className="font-semibold text-slate-800">{profile.name}</div>
            <div>Khóa {profile.cohort_year}</div>
            {result?.specialization_name && <div>Chuyên ngành: {result.specialization_name}</div>}
          </div>
        )}
        <p className="px-5 pb-5 text-[11px] leading-snug text-slate-400">
          Dữ liệu mẫu mô phỏng CTĐT 138 TC; cần đối chiếu với CTĐT và quy chế chính thức.
        </p>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <nav className="flex gap-1 overflow-x-auto border-b border-slate-200 bg-white px-2 py-2 md:hidden">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-xs font-medium whitespace-nowrap ${
                  isActive ? "bg-blue-50 text-blue-800" : "text-slate-600"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
