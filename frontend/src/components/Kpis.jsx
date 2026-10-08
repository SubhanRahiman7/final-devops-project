export default function Kpis({ stats }) {
  const cards = [
    { label: "Total tickets", value: stats.total, tone: "blue" },
    { label: "Open", value: stats.by_status.open, tone: "amber" },
    { label: "Urgent and unresolved", value: stats.open_urgent, tone: "red" },
    { label: "Resolution rate", value: `${stats.resolution_rate}%`, tone: "green" },
  ];
  return (
    <section className="kpis" aria-label="Key figures">
      {cards.map((card) => (
        <div key={card.label} className={`kpi ${card.tone}`}>
          <span className="kpi-label">{card.label}</span>
          <strong className="kpi-value">{card.value}</strong>
        </div>
      ))}
    </section>
  );
}
