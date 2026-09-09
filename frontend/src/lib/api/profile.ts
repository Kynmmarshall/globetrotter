import { apiFetch } from "./client";
import type { FavouriteResponse, Preferences, UserProfile } from "./types";

export function getMe() {
  return apiFetch<UserProfile>("/api/v1/users/me");
}

export function updateProfile(input: { display_name?: string; bio?: string; home_city?: string; locale?: string }) {
  return apiFetch<UserProfile>("/api/v1/users/me", { method: "PATCH", body: input });
}

export function updatePreferences(input: Preferences) {
  return apiFetch<UserProfile>("/api/v1/users/me/preferences", { method: "PUT", body: input });
}

export function listFavourites() {
  return apiFetch<FavouriteResponse[]>("/api/v1/users/me/favourites");
}

export function addFavourite(destinationId: string) {
  return apiFetch<FavouriteResponse>("/api/v1/users/me/favourites", {
    method: "POST",
    body: { destination_id: destinationId },
  });
}

export function removeFavourite(destinationId: string) {
  return apiFetch<void>(`/api/v1/users/me/favourites/${encodeURIComponent(destinationId)}`, { method: "DELETE" });
}
