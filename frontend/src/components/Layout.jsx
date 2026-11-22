import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../App.jsx";

const NAV = [
  { to: "/verify", label: "Verify", icon: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-7 9c.8-3.6 3.6-6 7-6s6.2 2.4 7 6" },
  { to: "/assistant", label: "Assistant", icon: "M4 5h16v11H8l-4 4V5Zm4 5h8M8 13h5" },
  { to: "/policies", label: "Policies", icon: "M6 3h9l4 4v14H6V3Zm9 0v4h4M9 12h7M9 16h7" },
  { to: "/employees", label: "Employees", admin: true, icon: "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm-6 9c.6-3 3-5 6-5s5.4 2 6 5m1-9a3 3 0 1 0 0-6m2 15c-.3-2-1.3-3.6-2.8-4.4" },
  { to: "/training", label: "Enrol & Train", admin: true, icon: "M4 19V9m6 10V5m6 14v-7m4 7H2" },
  { to: "/logs", label: "Logs", admin: true, icon: "M5 4h14v16H5V4Zm3 4h8M8 12h8M8 16h5" },
];

function Icon({ d }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

export default function Layout({ children }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const items = NAV.filter((n) => !n.admin || user.role === "admin");
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="34" height="34" />
          <div>
            <div className="brand-name">Orion Nexus</div>
            <div className="brand-sub">Employee Verification</div>
          </div>
        </div>
        <nav>
          {items.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
              <Icon d={n.icon} />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="who">
            <div className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</div>
            <div>
              <div className="who-name">{user.full_name}</div>
              <div className="who-role">{user.user_id} · {user.role}</div>
            </div>
          </div>
          <button className="btn ghost small" onClick={() => { signOut(); navigate("/login"); }}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
