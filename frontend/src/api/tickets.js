import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export const ticketsApi = {
  list: (params = {}) => api.get("/tickets/", { params }),
  create: (data) => api.post("/tickets/", data),
  update: (id, data) => api.patch(`/tickets/${id}/`, data),
  stats: () => api.get("/tickets/stats/"),
  classify: (description) => api.post("/tickets/classify/", { description }),
};
