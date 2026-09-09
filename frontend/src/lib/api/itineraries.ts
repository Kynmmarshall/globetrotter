import { apiFetch } from "./client";
import type { Itinerary, ItineraryItem, ItinerarySummary } from "./types";

export function listItineraries() {
  return apiFetch<ItinerarySummary[]>("/api/v1/itineraries");
}

export function getItinerary(id: string) {
  return apiFetch<Itinerary>(`/api/v1/itineraries/${id}`);
}

export interface PublicItinerary {
  title: string;
  start_date: string;
  end_date: string;
  currency: string;
  items: {
    day: number;
    position: number;
    scheduled_time: string | null;
    duration_minutes: number | null;
    destination_snapshot: ItineraryItem["destination_snapshot"];
  }[];
}

export function getPublicItinerary(token: string) {
  return apiFetch<PublicItinerary>(`/api/v1/public/itineraries/${token}`);
}

export function createItinerary(input: { title: string; start_date: string; end_date: string; currency?: string }) {
  return apiFetch<Itinerary>("/api/v1/itineraries", { method: "POST", body: input });
}

export function updateItinerary(
  id: string,
  input: Partial<{ title: string; start_date: string; end_date: string; currency: string }>,
) {
  return apiFetch<Itinerary>(`/api/v1/itineraries/${id}`, { method: "PATCH", body: input });
}

export function deleteItinerary(id: string) {
  return apiFetch<void>(`/api/v1/itineraries/${id}`, { method: "DELETE" });
}

export function addItineraryItem(
  itineraryId: string,
  input: {
    destination_id: string;
    day: number;
    scheduled_time?: string | null;
    duration_minutes?: number | null;
    notes?: string | null;
    estimated_cost?: number | null;
  },
) {
  return apiFetch<ItineraryItem>(`/api/v1/itineraries/${itineraryId}/items`, { method: "POST", body: input });
}

export function updateItineraryItem(
  itineraryId: string,
  itemId: string,
  input: Partial<{
    day: number;
    scheduled_time: string | null;
    duration_minutes: number | null;
    notes: string | null;
    estimated_cost: number | null;
  }>,
) {
  return apiFetch<ItineraryItem>(`/api/v1/itineraries/${itineraryId}/items/${itemId}`, {
    method: "PATCH",
    body: input,
  });
}

export function moveItineraryItem(itineraryId: string, itemId: string, direction: "up" | "down") {
  return apiFetch<Itinerary>(`/api/v1/itineraries/${itineraryId}/items/${itemId}/move`, {
    method: "POST",
    body: { direction },
  });
}

export function deleteItineraryItem(itineraryId: string, itemId: string) {
  return apiFetch<void>(`/api/v1/itineraries/${itineraryId}/items/${itemId}`, { method: "DELETE" });
}

export function createShareLink(itineraryId: string) {
  return apiFetch<{ token: string; revoked: boolean }>(`/api/v1/itineraries/${itineraryId}/share`, {
    method: "POST",
  });
}

export function revokeShareLink(itineraryId: string) {
  return apiFetch<void>(`/api/v1/itineraries/${itineraryId}/share`, { method: "DELETE" });
}
