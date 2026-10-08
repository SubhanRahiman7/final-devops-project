function ago(iso) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  return hours < 24 ? `${hours} h ago` : `${Math.round(hours / 24)} d ago`;
}

export default function ActivityFeed({ tickets }) {
  const latest = [...tickets]
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
    .slice(0, 6);
  return (
    <section className="panel">
      <h3>Recent activity</h3>
      <ul className="feed">
        {latest.map((t) => (
          <li key={t.id}>
            <span className={`dot s-${t.status}`} />
            <div>
              <div>{t.subject}</div>
              <div className="muted small">{t.status.replace("_", " ")} - {ago(t.updated_at)}</div>
            </div>
          </li>
        ))}
        {latest.length === 0 && <li className="muted">Nothing yet.</li>}
      </ul>
    </section>
  );
}
