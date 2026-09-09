import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, Navigation, MapPin, Plus } from "lucide-react";
import clsx from "clsx";
import * as destinationsApi from "@/lib/api/destinations";
import * as itinerariesApi from "@/lib/api/itineraries";
import { useFavourites } from "@/features/destinations/useFavourites";
import { useAuth } from "@/features/auth/AuthContext";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/States";
import { Button } from "@/components/ui/Button";
import { errorMessage } from "@/lib/api/errorMessage";

export function DestinationDetailPage() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { isFavourite, toggleFavourite } = useFavourites();
  const [selectedTripId, setSelectedTripId] = useState("");
  const [day, setDay] = useState(1);
  const queryClient = useQueryClient();

  const destinationQuery = useQuery({
    queryKey: ["destination", id],
    queryFn: () => destinationsApi.getDestination(id),
  });

  const tripsQuery = useQuery({
    queryKey: ["itineraries"],
    queryFn: itinerariesApi.listItineraries,
    enabled: Boolean(user),
  });

  const addToTripMutation = useMutation({
    mutationFn: () => itinerariesApi.addItineraryItem(selectedTripId, { destination_id: id, day }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["itinerary", selectedTripId] });
    },
  });

  if (destinationQuery.isLoading) return <Spinner label="Loading destination..." />;
  if (destinationQuery.isError || !destinationQuery.data) {
    return <ErrorState message={errorMessage(destinationQuery.error, "Destination not found.")} />;
  }

  const destination = destinationQuery.data;

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 md:px-8 md:py-10">
      <div className="aspect-[16/10] w-full overflow-hidden rounded-xl bg-border/40">
        <img
          src={destination.image.primary}
          alt={destination.image.alt}
          className="h-full w-full object-cover"
        />
      </div>

      <div className="mt-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="font-heading text-2xl font-bold">{destination.name}</h1>
          <p className="mt-1 flex items-center gap-1 text-sm text-ink/60">
            <MapPin size={14} aria-hidden="true" />
            {destination.city}, {destination.country}
          </p>
        </div>
        <button
          type="button"
          onClick={() => toggleFavourite(destination.id)}
          aria-pressed={isFavourite(destination.id)}
          aria-label="Save to favourites"
          className="shrink-0 rounded-full border border-border p-2.5 text-ink/60 hover:text-coral"
        >
          <Heart size={20} className={clsx(isFavourite(destination.id) && "fill-coral text-coral")} />
        </button>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-ink/80">{destination.description}</p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button onClick={() => navigate(`/map?destination=${destination.id}`)}>
          <Navigation size={16} aria-hidden="true" />
          Get directions
        </Button>
      </div>

      {user ? (
        <section className="mt-8 rounded-lg border border-border bg-surface p-4">
          <h2 className="font-heading text-sm font-semibold">Add to a trip</h2>
          {tripsQuery.data && tripsQuery.data.length > 0 ? (
            <div className="mt-3 flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
                Trip
                <select
                  value={selectedTripId}
                  onChange={(event) => setSelectedTripId(event.target.value)}
                  className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
                >
                  <option value="">Select a trip...</option>
                  {tripsQuery.data.map((trip) => (
                    <option key={trip.id} value={trip.id}>
                      {trip.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
                Day
                <input
                  type="number"
                  min={1}
                  value={day}
                  onChange={(event) => setDay(Number(event.target.value))}
                  className="w-20 rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
                />
              </label>
              <Button disabled={!selectedTripId || addToTripMutation.isPending} onClick={() => addToTripMutation.mutate()}>
                <Plus size={16} aria-hidden="true" />
                Add stop
              </Button>
            </div>
          ) : (
            <p className="mt-2 text-sm text-ink/60">
              You don't have any trips yet.{" "}
              <Link to="/trips" className="font-semibold text-primary underline underline-offset-2">
                Create one
              </Link>{" "}
              first.
            </p>
          )}
          {addToTripMutation.isSuccess ? <p className="mt-2 text-xs text-primary">Added to your trip.</p> : null}
          {addToTripMutation.isError ? (
            <p className="mt-2 text-xs text-coral">{errorMessage(addToTripMutation.error)}</p>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
