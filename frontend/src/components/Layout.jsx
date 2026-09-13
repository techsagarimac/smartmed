import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Bell, Camera, ClipboardList, HeartPulse, LayoutDashboard, LogOut, Pill, Users } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { useReminders } from "../hooks/useReminders";
import { formatClock } from "../utils/dates";
import { SafetyNotice } from "./SafetyNotice";

const LINKS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/medicines", label: "Medicines", icon: Pill },
  { to: "/scan", label: "Scan & verify", icon: Camera },
  { to: "/history", label: "Dose history", icon: ClipboardList },
  { to: "/caregivers", label: "Caregivers", icon: Users },
  { to: "/about", label: "About & safety", icon: HeartPulse },
];

export function Layout() {
  const { user, logout, isAuthenticated } = useAuth();
  const { due } = useReminders(isAuthenticated);
  const [open, setOpen] = useState(false);
  const notified = useRef(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    if (!due.length || typeof Notification === "undefined" || Notification.permission !== "granted") return;
    due.forEach((item) => {
      const key = `${item.medicine_id}-${item.scheduled_time}`;
      if (notified.current.has(key)) return;
      notified.current.add(key);
      new Notification("SmartMed reminder", {
        body: `${item.medicine_name} is scheduled for ${formatClock(item.scheduled_time)}. Verify the package before recording the dose.`,
      });
    });
  }, [due]);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">SM</div>
          <h1 className="brand-title">SmartMed</h1>
          <p className="brand-sub">Reminder & package verification</p>
        </div>
        <nav className="nav">
          {LINKS.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink key={link.to} to={link.to} end={link.end} onClick={() => setOpen(false)}>
                <Icon size={18} />
                {link.label}
                {link.to === "/" && due.length ? <span className="nav-count">{due.length}</span> : null}
              </NavLink>
            );
          })}
        </nav>
        <div className="sidebar-user">
          <strong>{user?.name}</strong>
          <span>{user?.email}</span>
          <button
            type="button"
            className="btn btn-ghost btn-small"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
        <div className="sidebar-foot">
          Compares saved records only. Not a diagnosis or prescribing tool.
        </div>
      </aside>
      <main className="main">
        <div className="topbar">
          <button type="button" className="menu-btn" onClick={() => setOpen((value) => !value)}>
            Menu
          </button>
          {due.length ? (
            <div className="reminder-chip">
              <Bell size={16} />
              {due.length} reminder{due.length === 1 ? "" : "s"} waiting
              <button type="button" className="btn btn-small btn-primary" onClick={() => navigate("/scan")}>
                Verify
              </button>
            </div>
          ) : (
            <span className="muted">No due reminders right now</span>
          )}
        </div>
        {due.length ? (
          <div className="banner banner-warn">
            A saved schedule is due. Open Scan & verify, compare the package with your saved medicine, then
            record the dose if it appears to match.
          </div>
        ) : null}
        <Outlet />
        <SafetyNotice compact />
      </main>
    </div>
  );
}
