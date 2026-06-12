import { ref } from "vue";
import router from "../router";

const defaultApiBase = import.meta.env.VITE_API_BASE || "http://119.45.182.166:3784";
export const apiBase = ref(localStorage.getItem("homeShopApiBase") || defaultApiBase);
export const token = ref(localStorage.getItem("homeShopAdminToken") || "");
export const currentAdmin = ref(null);

export function setApiBase(url) {
  const cleaned = url.replace(/\/$/, "");
  apiBase.value = cleaned;
  localStorage.setItem("homeShopApiBase", cleaned);
}

export function setToken(t) {
  token.value = t;
  localStorage.setItem("homeShopAdminToken", t);
}

export function clearToken() {
  token.value = "";
  currentAdmin.value = null;
  localStorage.removeItem("homeShopAdminToken");
}

export async function request(path, options = {}) {
  const response = await fetch(`${apiBase.value}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token.value ? { Authorization: `Bearer ${token.value}` } : {}),
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      router.push("/login");
    }
    throw new Error(payload.error || "请求失败");
  }
  return payload.data ?? payload;
}

export function yuan(cents) {
  return (Number(cents || 0) / 100).toFixed(2);
}

export function formatTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}
