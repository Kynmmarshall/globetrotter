import { apiFetch } from "./client";
import type { Destination, DestinationListResponse, RecommendationListResponse } from "./types";

export function listDestinations(params: { q?: string; category?: string; limit?: number; offset?: number } = {}) {
  const query = new URLSearchParams();
  if (params.q) query.set("q", params.q);
  if (params.category) query.set("category", params.category);
  query.set("limit", String(params.limit ?? 20));
  query.set("offset", String(params.offset ?? 0));
  return apiFetch<DestinationListResponse>(`/api/v1/destinations?${query.toString()}`);
}

export function getDestination(id: string) {
  return apiFetch<Destination>(`/api/v1/destinations/${encodeURIComponent(id)}`);
}

export function getRecommendations(limit = 10) {
  return apiFetch<RecommendationListResponse>(`/api/v1/recommendations?limit=${limit}`);
}
