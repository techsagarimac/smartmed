const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

function token() {
  return localStorage.getItem("smartmed_token");
}

async function parseError(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.errors) && body.errors[0]) return body.errors[0];
  } catch {
    /* still use the status text below */
  }
  return `Request failed (${response.status})`;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const isForm = options.body instanceof FormData;
  if (!isForm && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const auth = token();
  if (auth) headers.set("Authorization", `Bearer ${auth}`);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch {
    throw new Error("Network error. Check that the SmartMed API is running.");
  }

  if (response.status === 401) {
    const message = await parseError(response);
    const error = new Error(message);
    error.status = 401;
    throw error;
  }

  if (!response.ok) {
    const error = new Error(await parseError(response));
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) return null;
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export const api = {
  health: () => request("/health"),
  register: (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => request("/auth/me"),
  medicines: () => request("/medicines"),
  medicine: (id) => request(`/medicines/${id}`),
  createMedicine: (payload) => request("/medicines", { method: "POST", body: JSON.stringify(payload) }),
  updateMedicine: (id, payload) => request(`/medicines/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteMedicine: (id) => request(`/medicines/${id}`, { method: "DELETE" }),
  schedules: () => request("/schedules"),
  createSchedule: (payload) => request("/schedules", { method: "POST", body: JSON.stringify(payload) }),
  updateSchedule: (id, payload) => request(`/schedules/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSchedule: (id) => request(`/schedules/${id}`, { method: "DELETE" }),
  scan: (formData) => request("/verification/scan", { method: "POST", body: formData }),
  doseHistory: () => request("/dose-history"),
  recordDose: (payload) => request("/dose-history", { method: "POST", body: JSON.stringify(payload) }),
  analytics: () => request("/analytics"),
  reminders: () => request("/reminders"),
  caregivers: () => request("/caregivers"),
  createCaregiver: (payload) => request("/caregivers", { method: "POST", body: JSON.stringify(payload) }),
  updateCaregiver: (id, payload) => request(`/caregivers/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteCaregiver: (id) => request(`/caregivers/${id}`, { method: "DELETE" }),
  caregiverDelivery: () => request("/caregivers/status/delivery"),
};
