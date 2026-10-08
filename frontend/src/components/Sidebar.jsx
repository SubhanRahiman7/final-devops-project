const NAV = [
  ["Dashboard", true],
  ["Tickets", false],
  ["Customers", false],
  ["Reports", false],
  ["Settings", false],
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">H</span>
        <span>HelpDesk</span>
      </div>
      <p className="nav-label">Workspace</p>
      <nav>
        {NAV.map(([label, active]) => (
          <a key={label} href="#" className={active ? "nav-item active" : "nav-item"} onClick={(e) => e.preventDefault()}>
            {label}
          </a>
        ))}
      </nav>
      <div className="sidebar-foot">
        <span className="dot" /> Production cluster
      </div>
    </aside>
  );
}
