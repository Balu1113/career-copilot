import { Outlet } from "react-router-dom";

import Sidebar from "./Sidebar";

function AppLayout() {
  return (
    <div className="dashboard-layout">
      <Sidebar />

      <Outlet />
    </div>
  );
}

export default AppLayout;
