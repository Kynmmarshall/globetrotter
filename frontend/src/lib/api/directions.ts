import { apiFetch } from "./client";
import type { DirectionsResponse, DirectionsWaypoint } from "./types";

export function getDirections(input: { start: DirectionsWaypoint; stops: DirectionsWaypoint[] }) {
  return apiFetch<DirectionsResponse>("/api/v1/directions", {
    method: "POST",
    body: { profile: "driving", ...input },
  });
}
