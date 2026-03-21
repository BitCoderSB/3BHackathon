import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import VideoFeedPiP from "./VideoFeedPiP";

export default function Layout() {
  const location = useLocation();
  const isLivePanel = location.pathname === "/";

  return (
    <div className="flex min-h-screen bg-surface-page">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
      {/* PiP solo se muestra fuera del panel en vivo */}
      {!isLivePanel && <VideoFeedPiP />}
    </div>
  );
}
