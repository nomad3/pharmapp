import axios from "axios";

const client = axios.create({ baseURL: "/api/v1" });

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;

  const orgId = localStorage.getItem("org_id");
  if (orgId) config.headers["X-Org-Id"] = orgId;

  return config;
});

export default client;
