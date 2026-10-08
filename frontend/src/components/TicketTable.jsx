const STATUS_LABEL = { open: "Open", in_progress: "In progress", resolved: "Resolved" };
const NEXT_STATUS = { open: "in_progress", in_progress: "resolved", resolved: "open" };

export default function TicketTable({ tickets, onAdvance, onDelete }) {
  if (tickets.length === 0) {
    return <p className="empty">No tickets in this view.</p>;
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Subject</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Assignee</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id}>
              <td className="muted">{t.id}</td>
              <td>
                <div className="subject">{t.subject}</div>
                <div className="muted small">{t.requester || "no requester"}</div>
              </td>
              <td className="cap">{t.category}</td>
              <td><span className={`badge p-${t.priority}`}>{t.priority}</span></td>
              <td><span className={`badge s-${t.status}`}>{STATUS_LABEL[t.status]}</span></td>
              <td>{t.assignee || <span className="muted">unassigned</span>}</td>
              <td className="actions">
                <button className="link" onClick={() => onAdvance(t)} title="Move to the next status">
                  {STATUS_LABEL[NEXT_STATUS[t.status]]}
                </button>
                <button className="link danger" onClick={() => onDelete(t)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
