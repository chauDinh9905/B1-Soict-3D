/**
 * Lớp DUY NHẤT trong frontend gọi backend. Feature không tự gọi fetch tới server.
 * Nếu backend không chạy (hoặc bản deploy chỉ có frontend), dữ liệu NỘI DUNG tự lấy từ JSON tĩnh trong public/data.
 * Tài khoản thì không có dự phòng tĩnh: backend tắt -> me() trả null, các hàm ghi trả { ok:false, offline:true }.
 * Cookie phiên (sid, HttpOnly) do trình duyệt tự gửi vì /api cùng tên miền (proxy Vite khi dev, vercel.json khi deploy).
 * Hợp đồng API: docs/API.md
 */
export class ApiClient {
  constructor(config) {
    this.base = config.API_URL;
    this.staticBase = config.STATIC_DATA_URL;
    this.online = true;
  }

  async _get(path, staticPath) {
    if (this.online) {
      try {
        const res = await fetch(`${this.base}${path}`, { credentials: 'same-origin' });
        if (res.ok) return await res.json();
        throw new Error(`HTTP ${res.status}`);
      } catch (err) {
        console.warn(`[api] ${path} lỗi (${err.message}) -> dùng dữ liệu tĩnh`);
        this.online = false;
      }
    }
    const res = await fetch(`${this.staticBase}${staticPath}`);
    if (!res.ok) throw new Error(`Không tải được ${staticPath}`);
    return res.json();
  }

  getCampus() { return this._get('/campus', '/campus.json'); }
  getBuilding(id) { return this._get(`/buildings/${id}`, `/buildings/${id}.json`); }

  /** Gửi request ghi dữ liệu. Luôn trả { ok, status, data } – không ném lỗi, để UI tự hiện data.error. */
  async _send(method, path, body) {
    if (!this.online) return { ok: false, offline: true, status: 0, data: null };
    try {
      const res = await fetch(`${this.base}${path}`, {
        method,
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },   // backend chỉ nhận JSON (chống CSRF)
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      return { ok: res.ok, status: res.status, data: await res.json().catch(() => null) };
    } catch {
      return { ok: false, offline: true, status: 0, data: null };
    }
  }

  _post(path, body) { return this._send('POST', path, body); }

  sendFeedback({ name, message, poiId }) { return this._post('/feedback', { name, message, poiId }); }
  trackVisit() { return this._post('/stats/visit', {}).catch(() => {}); }

  // ---- Tài khoản (xem docs/API.md – phần /auth) ----
  register({ email, password, displayName }) { return this._post('/auth/register', { email, password, displayName }); }
  login({ email, password }) { return this._post('/auth/login', { email, password }); }
  logout() { return this._post('/auth/logout'); }

  /** User đang đăng nhập, hoặc null (chưa đăng nhập / backend tắt). */
  async me() {
    if (!this.online) return null;
    try {
      const res = await fetch(`${this.base}/auth/me`, { credentials: 'same-origin' });
      return res.ok ? (await res.json()).user : null;
    } catch {
      return null;
    }
  }
}
