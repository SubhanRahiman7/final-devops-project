// The browser only knows relative URLs. nginx (compose) and the Ingress (Kubernetes) route /api to the backend.
async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${options.method || "GET"} ${path} failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  listTickets: (status) => request(`/api/tickets${status && status !== "all" ? `?status=${status}` : ""}`),
  stats: () => request("/api/tickets/stats"),
  createTicket: (payload) => request("/api/tickets", { method: "POST", body: JSON.stringify(payload) }),
  updateTicket: (id, payload) => request(`/api/tickets/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteTicket: (id) => request(`/api/tickets/${id}`, { method: "DELETE" }),
};
