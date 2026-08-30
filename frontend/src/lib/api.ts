import axios, { AxiosInstance, AxiosError } from "axios";

const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000/api";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: false,
});

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("access_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

let refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original: any = error.config;
    if (error.response?.status === 401 && !original.__isRetry) {
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          if (!refreshing) {
            refreshing = axios
              .post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
              .then((r) => {
                localStorage.setItem("access_token", r.data.access_token);
                return r.data.access_token as string;
              })
              .finally(() => {
                refreshing = null;
              });
          }
          const newToken = await refreshing;
          original.__isRetry = true;
          original.headers.Authorization = `Bearer ${newToken}`;
          return api.request(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { BASE_URL };
