import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api";

const api = axios.create({ baseURL: API_BASE_URL });
let refreshPromise = null;

const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

const redirectToLogin = () => {
  const publicPath = ["/login", "/register", "/forgot-password"];
  if (
    !publicPath.includes(window.location.pathname) &&
    !window.location.pathname.startsWith("/reset-password/")
  ) {
    window.location.href = "/login";
  }
};

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    const requestUrl = config.url || "";
    const authEndpoint = /\/auth\/(login|register|refresh|logout|password\/reset)/.test(
      requestUrl,
    );
    if (token && !authEndpoint) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const request = error.config;
    const requestUrl = request?.url || "";
    const authEndpoint = /\/auth\/(login|register|refresh|logout|password\/reset)/.test(
      requestUrl,
    );

    if (error.response?.status !== 401 || !request || authEndpoint) {
      return Promise.reject(error);
    }

    if (request._retry) {
      clearTokens();
      redirectToLogin();
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
      clearTokens();
      redirectToLogin();
      return Promise.reject(error);
    }

    request._retry = true;

    if (!refreshPromise) {
      refreshPromise = axios
        .post(`${API_BASE_URL}/auth/refresh/`, { refresh: refreshToken })
        .then(({ data }) => {
          localStorage.setItem("access_token", data.access);
          localStorage.setItem("refresh_token", data.refresh);
          return data.access;
        })
        .catch((refreshError) => {
          clearTokens();
          redirectToLogin();
          throw refreshError;
        })
        .finally(() => {
          refreshPromise = null;
        });
    }

    return refreshPromise.then((accessToken) => {
      request.headers.Authorization = `Bearer ${accessToken}`;
      return api(request);
    });
  },
);

export default api;