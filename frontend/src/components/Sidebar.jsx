import { useState } from "react";
import {
  BarChart3,
  Brain,
  BriefcaseBusiness,
  CircleHelp,
  FileText,
  History,
  Map,
  Menu,
  MessageSquare,
  Sparkles,
  X,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import { ONBOARDING_OPEN_EVENT } from "./OnboardingTour";

const NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      { label: "Dashboard", path: "/dashboard", icon: BarChart3 },
      { label: "My Resumes", path: "/resumes", icon: FileText },
      { label: "Resume Builder", path: "/resume-builder", icon: FileText },
      { label: "Jobs", path: "/jobs", icon: BriefcaseBusiness },
      { label: "Recommended Jobs", path: "/recommended-jobs", icon: Sparkles },
      { label: "Applications", path: "/applications", icon: BriefcaseBusiness },
    ],
  },
  {
    label: "Career",
    items: [
      { label: "Career Analysis", path: "/career-analysis", icon: Sparkles },
      { label: "Career History", path: "/career-history", icon: History },
      { label: "Career Roadmap", path: "/career-roadmap", icon: Map },
      { label: "Resume Intelligence", path: "/resume-intelligence", icon: Brain },
      { label: "Resume AI Chat", path: "/resume-chat", icon: MessageSquare },
    ],
  },
  {
    label: "Interview",
    items: [
      { label: "Interview Prep", path: "/interview-prep", icon: MessageSquare },
      { label: "Interview Simulator", path: "/interview-simulator", icon: MessageSquare },
      { label: "Interview Performance", path: "/interview-performance", icon: BarChart3 },
      { label: "Interview History", path: "/interview-history", icon: History },
    ],
  },
];

const PRIMARY_PATHS = new Set([
  "/dashboard",
  "/resumes",
  "/jobs",
  "/applications",
]);

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigateTo = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const openGuide = () => {
    window.dispatchEvent(new Event(ONBOARDING_OPEN_EVENT));
    setMobileOpen(false);
  };

  const renderItem = ({ label, path, icon: Icon }, mobile = false) => {
    const active = location.pathname === path ||
      (path !== "/" && location.pathname.startsWith(`${path}/`));

    return (
      <button
        key={path}
        type="button"
        className={`nav-item ${active ? "active" : ""}`}
        aria-current={active ? "page" : undefined}
        onClick={() => navigateTo(path)}
      >
        <Icon size={18} />
        <span>{label}</span>
        {mobile && active && <span className="mobile-nav-current">Current</span>}
      </button>
    );
  };

  const mobileGroups = NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !PRIMARY_PATHS.has(item.path)),
  })).filter((group) => group.items.length > 0);

  return (
    <>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Sparkles size={22} />
          <span>Career Copilot</span>
        </div>

        <button className="nav-item sidebar-guide" type="button" onClick={openGuide}>
          <CircleHelp size={18} />
          <span>Getting Started</span>
        </button>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {NAV_GROUPS.map((group) => (
            <div className="sidebar-nav-group" key={group.label}>
              <h2>{group.label}</h2>
              {group.items.map((item) => renderItem(item))}
            </div>
          ))}
        </nav>
      </aside>

      {mobileOpen && (
        <>
          <button
            className="mobile-nav-backdrop"
            type="button"
            aria-label="Close navigation menu"
            onClick={() => setMobileOpen(false)}
          />
          <div className="mobile-nav-panel" id="mobile-navigation-panel">
            <button className="nav-item" type="button" onClick={openGuide}>
              <CircleHelp size={18} />
              <span>Getting Started</span>
            </button>
            {mobileGroups.map((group) => (
              <section className="mobile-nav-group" key={group.label}>
                <h2>{group.label}</h2>
                {group.items.map((item) => renderItem(item, true))}
              </section>
            ))}
          </div>
        </>
      )}

      <nav className="mobile-nav" aria-label="Mobile navigation">
        {NAV_GROUPS[0].items
          .filter((item) => PRIMARY_PATHS.has(item.path))
          .map((item) => renderItem(item, true))}
        <button
          className={`nav-item mobile-more ${mobileOpen ? "active" : ""}`}
          type="button"
          aria-expanded={mobileOpen}
          aria-controls="mobile-navigation-panel"
          onClick={() => setMobileOpen((open) => !open)}
        >
          {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          <span>{mobileOpen ? "Close" : "More"}</span>
        </button>
      </nav>
    </>
  );
}

export default Sidebar;