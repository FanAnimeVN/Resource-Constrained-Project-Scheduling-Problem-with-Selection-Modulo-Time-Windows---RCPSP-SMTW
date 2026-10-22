import { Suspense, lazy } from "react";
import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import { Spinner } from "./components/ui";
import AdvisorPage from "./pages/AdvisorPage";
import NextTermPage from "./pages/NextTermPage";
import PlansPage from "./pages/PlansPage";
import ProfilePage from "./pages/ProfilePage";

// Trang dùng thư viện biểu đồ/đồ thị lớn được tải khi cần.
const ComparePage = lazy(() => import("./pages/ComparePage"));
const DataPage = lazy(() => import("./pages/DataPage"));

export default function App() {
  return (
    <Suspense fallback={<Spinner label="Đang tải…" />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<ProfilePage />} />
          <Route path="plans" element={<PlansPage />} />
          <Route path="compare" element={<ComparePage />} />
          <Route path="advisor" element={<AdvisorPage />} />
          <Route path="next-term" element={<NextTermPage />} />
          <Route path="data" element={<DataPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
