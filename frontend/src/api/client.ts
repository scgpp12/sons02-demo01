import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({ baseURL });

const TOKEN_KEY = "ses_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// 全リクエストに Authorization を付与
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 401 は自動でログインへ
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      clearToken();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

/** バックエンドのエラー詳細を取り出す。 */
export function errMessage(error: unknown, fallback = "エラーが発生しました"): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail.map((d) => d.msg).join(", ");
  }
  return fallback;
}
