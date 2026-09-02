import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ControlPage } from "@/pages/ControlPage";
import { Dashboard } from "@/pages/Dashboard";
import { HelpPage } from "@/pages/HelpPage";
import { InfoPage } from "@/pages/InfoPage";
import Logging from "@/pages/Logging";
import { RecordingPage } from "@/pages/RecordingPage";
import { SessionPage } from "@/pages/SessionPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ViewerPage } from "@/pages/ViewerPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="info" element={<InfoPage />} />
          <Route path="session" element={<SessionPage />} />
          <Route path="control" element={<ControlPage />} />
          <Route path="viewer" element={<ViewerPage />} />
          <Route path="recording" element={<RecordingPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="help" element={<HelpPage />} />
          <Route path="logging" element={<Logging />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
