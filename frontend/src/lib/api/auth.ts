import { apiFetch } from "./client";

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  csrf_token: string;
}

export function register(input: { email: string; password: string; display_name: string }) {
  return apiFetch<TokenResponse>("/api/v1/auth/register", { method: "POST", body: input });
}

export function login(input: { email: string; password: string }) {
  return apiFetch<TokenResponse>("/api/v1/auth/login", { method: "POST", body: input });
}

export function logout() {
  return apiFetch<void>("/api/v1/auth/logout", { method: "POST" });
}

export function refresh() {
  return apiFetch<TokenResponse>("/api/v1/auth/refresh", { method: "POST" });
}
