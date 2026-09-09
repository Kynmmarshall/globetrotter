import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import { LocateFixed, Navigation } from "lucide-react";
import * as destinationsApi from "@/lib/api/destinations";
import * as directionsApi from "@/lib/api/directions";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/States";
import { Button } from "@/components/ui/Button";
import { errorMessage } from "@/lib/api/errorMessage";
import type { DirectionsWaypoint } from "@/lib/api/types";

// Vite bundles Leaflet's default marker images with hashed filenames, which
// breaks Leaflet's CSS-relative default icon URLs -- point at the imported
// assets explicitly instead.
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const YAOUNDE_CENTER: [number, number] = [3.848, 11.502];

function FitToRoute({ geometry }: { geometry: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (geometry.length === 0) return;
    const bounds = L.latLngBounds(geometry.map(([lng, lat]) => [lat, lng]));
    map.fitBounds(bounds, { padding: [32, 32] });
  }, [geometry, map]);
  return null;
}

export function MapPage() {
  const [searchParams] = useSearchParams();
  const destinationId = searchParams.get("destination");
  const [start, setStart] = useState<DirectionsWaypoint | null>(null);
  const [locating, setLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);

  const destinationsQuery = useQuery({
    queryKey: ["destinations", "all"],
    queryFn: () => destinationsApi.listDestinations({ limit: 100 }),
  });

  const destinations = destinationsQuery.data?.items ?? [];
  const selectedDestination = destinations.find((d) => d.id === destinationId) ?? null;

  const directionsQuery = useQuery({
    queryKey: ["directions", destinationId, start],
    queryFn: () =>
      directionsApi.getDirections({ start: start!, stops: [{ destination_id: destinationId! }] }),
    enabled: Boolean(start && destinationId),
  });

  const requestCurrentLocation = () => {
    setLocationError(null);
    if (!("geolocation" in navigator)) {
      setLocationError("Your browser does not support location access. Try searching for a starting address instead.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setStart({ lat: position.coords.latitude, lng: position.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocationError("Location access was denied. Pick a destination as your starting point instead.");
        setLocating(false);
      },
      { timeout: 10_000 },
    );
  };

  const routeGeometry = useMemo<[number, number][]>(
    () => directionsQuery.data?.geometry.map(([lng, lat]) => [lat, lng] as [number, number]) ?? [],
    [directionsQuery.data],
  );

  return (
    <div className="flex h-dvh flex-col md:flex-row">
      <div className="relative flex-1">
        <MapContainer center={YAOUNDE_CENTER} zoom={13} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {destinations.map((destination) => (
            <Marker key={destination.id} position={[destination.lat, destination.lng]}>
              <Popup>
                <div className="text-sm font-semibold">{destination.name}</div>
                <div className="text-xs text-ink/60">{destination.category}</div>
              </Popup>
            </Marker>
          ))}
          {routeGeometry.length > 0 ? (
            <>
              <Polyline positions={routeGeometry} pathOptions={{ color: "#3D66DB", weight: 5 }} />
              <FitToRoute geometry={directionsQuery.data!.geometry} />
            </>
          ) : null}
        </MapContainer>
      </div>

      <aside className="w-full shrink-0 overflow-y-auto border-t border-border bg-surface p-4 md:w-80 md:border-l md:border-t-0">
        {destinationsQuery.isLoading ? <Spinner label="Loading map data..." /> : null}
        {destinationsQuery.isError ? <ErrorState message={errorMessage(destinationsQuery.error)} /> : null}

        {selectedDestination ? (
          <div>
            <h2 className="font-heading text-lg font-semibold">Directions to {selectedDestination.name}</h2>
            {!start ? (
              <div className="mt-3">
                <Button onClick={requestCurrentLocation} disabled={locating}>
                  <LocateFixed size={16} aria-hidden="true" />
                  {locating ? "Locating..." : "Use my current location"}
                </Button>
                {locationError ? <p className="mt-2 text-xs text-coral">{locationError}</p> : null}
              </div>
            ) : (
              <>
                {directionsQuery.isLoading ? <Spinner label="Finding a route..." /> : null}
                {directionsQuery.isError ? (
                  <ErrorState message={errorMessage(directionsQuery.error, "No route could be found.")} />
                ) : null}
                {directionsQuery.data ? (
                  <div className="mt-3">
                    <p className="text-sm font-medium">
                      <Navigation size={14} className="mr-1 inline" aria-hidden="true" />
                      {(directionsQuery.data.distance_meters / 1000).toFixed(1)} km &middot;{" "}
                      {Math.round(directionsQuery.data.duration_seconds / 60)} min drive
                    </p>
                    <ol className="mt-3 space-y-2 text-sm">
                      {directionsQuery.data.steps.map((step, index) => (
                        <li key={index} className="border-b border-border pb-2 last:border-none">
                          {step.instruction}
                        </li>
                      ))}
                    </ol>
                  </div>
                ) : null}
              </>
            )}
          </div>
        ) : (
          <p className="text-sm text-ink/60">
            Select a destination from Explore and choose "Get directions" to see a driving route here.
          </p>
        )}
      </aside>
    </div>
  );
}
