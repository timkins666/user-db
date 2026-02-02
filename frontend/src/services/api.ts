import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { token } from "../auth/authToken";
import { refreshAccessToken } from "../auth/authApi";
import { API_URL } from "../config/constants";

interface RetryableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let isRefreshing = false;

let refreshQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const enqueueRefresh = (): Promise<string> => {
  return new Promise((resolve, reject) => {
    refreshQueue.push({ resolve, reject });
  });
};

const resolveQueue = (token: string) => {
  refreshQueue.forEach((p) => p.resolve(token));
  refreshQueue = [];
};

const rejectQueue = (err: unknown) => {
  refreshQueue.forEach((p) => p.reject(err));
  refreshQueue = [];
};

export const api = axios.create({
  baseURL: API_URL,
  // withCredentials: true,
});

// Attach access token on every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (config.url?.includes("/auth/")) {
    return config;
  }

  const accessToken = token.getAccessToken();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Handle 401 + refresh logic
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig;

    if (
      error.response?.status === 401 &&
      originalRequest.url?.includes("/auth/")
    ) {
      console.debug("auth error on auth request, not retrying");
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        // Wait for in-flight refresh
        console.debug("waiting for ongoing token refresh");
        const newToken = await enqueueRefresh();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        console.debug("token refreshed - retrying");
        return api(originalRequest);
      }

      isRefreshing = true;

      try {
        console.debug("refreshing access token");

        const newToken = await refreshAccessToken();
        resolveQueue(newToken);

        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (err) {
        rejectQueue(err);
        console.debug("refresh failed, redirecting to login");
        // refresh failed
        token.setAccessToken(null);
        alert("Session expired. Please log in again.");
        window.location.href = "/login";
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
