// Small fetch wrapper: adds the login token, turns errors into readable messages,
// and logs the user out when the token has expired.
const TOKEN_KEY = "evp_token";
const USER_KEY = "evp_user";

export const session = {
  get token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  get user() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY));
    } catch {
      return null;
    }
  },
  save(data) {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({ user_id: data.user_id, full_name: data.full_name, role: data.role }));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, form, raw } = {}) {
  const headers = {};
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(path, { method, headers, body: payload });
  if (res.status === 401 && !path.endsWith("/auth/login")) {
    session.clear();
    window.location.assign("/login");
    throw new ApiError("Session expired. Please sign in again.", 401);
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") msg = data.detail;
      else if (Array.isArray(data.detail)) msg = data.detail.map((d) => d.msg).join("; ");
    } catch {
      /* not JSON */
    }
    throw new ApiError(msg, res.status);
  }
  if (raw) return res;
  return res.status === 204 ? null : res.json();
}

export const api = {
  login(userId, password) {
    const form = new URLSearchParams({ username: userId, password });
    return fetch("/api/auth/login", { method: "POST", body: form }).then(async (res) => {
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new ApiError(data.detail || "Login failed", res.status);
      return data;
    });
  },
  get: (p) => request(p),
  post: (p, body) => request(p, { method: "POST", body }),
  patch: (p, body) => request(p, { method: "PATCH", body }),
  del: (p) => request(p, { method: "DELETE" }),
  upload: (p, form) => request(p, { method: "POST", form }),
  blob: (p) => request(p, { raw: true }).then((r) => r.blob()),
};

export function filesForm(field, files) {
  const form = new FormData();
  for (const f of files) form.append(field, f, f.webkitRelativePath || f.name);
  return form;
}
