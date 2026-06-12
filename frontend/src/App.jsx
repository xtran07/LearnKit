import { NavLink, Route, Routes } from "react-router-dom";
import ResumePage from "./pages/ResumePage.jsx";
import TopicsPage from "./pages/TopicsPage.jsx";
import StudyPage from "./pages/StudyPage.jsx";
import ProgressPage from "./pages/ProgressPage.jsx";

const navLinkClass = ({ isActive }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${
    isActive ? "bg-indigo-600 text-white" : "text-gray-600 hover:bg-gray-100"
  }`;

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <nav className="max-w-4xl mx-auto px-4 py-3 flex gap-2">
          <span className="font-semibold text-lg mr-4">Interview Prep Tracker</span>
          <NavLink to="/" className={navLinkClass} end>
            Resume
          </NavLink>
          <NavLink to="/topics" className={navLinkClass}>
            Topics
          </NavLink>
          <NavLink to="/study" className={navLinkClass}>
            Study
          </NavLink>
          <NavLink to="/progress" className={navLinkClass}>
            Progress
          </NavLink>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<ResumePage />} />
          <Route path="/topics" element={<TopicsPage />} />
          <Route path="/study" element={<StudyPage />} />
          <Route path="/progress" element={<ProgressPage />} />
        </Routes>
      </main>
    </div>
  );
}
