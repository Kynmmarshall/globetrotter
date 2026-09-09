import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUp, ArrowDown, Trash2, Share2, Link as LinkIcon, Plus } from "lucide-react";
import * as itinerariesApi from "@/lib/api/itineraries";
import * as destinationsApi from "@/lib/api/destinations";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/States";
import { errorMessage } from "@/lib/api/errorMessage";
import clsx from "clsx";

export function TripPlannerPage() {
  const { id = "" } = useParams();
  const queryClient = useQueryClient();
  const [activeDay, setActiveDay] = useState(1);
  const [copiedLink, setCopiedLink] = useState(false);
  const [newStopDestinationId, setNewStopDestinationId] = useState("");

  const tripQuery = useQuery({ queryKey: ["itinerary", id], queryFn: () => itinerariesApi.getItinerary(id) });
  const destinationsQuery = useQuery({
    queryKey: ["destinations", "picker"],
    queryFn: () => destinationsApi.listDestinations({ limit: 100 }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["itinerary", id] });

  const addItemMutation = useMutation({
    mutationFn: () => itinerariesApi.addItineraryItem(id, { destination_id: newStopDestinationId, day: activeDay }),
    onSuccess: () => {
      invalidate();
      setNewStopDestinationId("");
    },
  });

  const moveMutation = useMutation({
    mutationFn: ({ itemId, direction }: { itemId: string; direction: "up" | "down" }) =>
      itinerariesApi.moveItineraryItem(id, itemId, direction),
    onSuccess: invalidate,
  });
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: string) => itinerariesApi.deleteItineraryItem(id, itemId),
    onSuccess: invalidate,
  });
  const shareMutation = useMutation({
    mutationFn: () => itinerariesApi.createShareLink(id),
    onSuccess: invalidate,
  });
  const revokeShareMutation = useMutation({
    mutationFn: () => itinerariesApi.revokeShareLink(id),
    onSuccess: invalidate,
  });

  const days = useMemo(() => {
    const trip = tripQuery.data;
    if (!trip) return [1];
    const start = new Date(trip.start_date);
    const end = new Date(trip.end_date);
    const dayCount = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1);
    return Array.from({ length: dayCount }, (_, index) => index + 1);
  }, [tripQuery.data]);

  if (tripQuery.isLoading) return <Spinner label="Loading trip..." />;
  if (tripQuery.isError || !tripQuery.data) {
    return <ErrorState message={errorMessage(tripQuery.error, "Trip not found.")} />;
  }

  const trip = tripQuery.data;
  const itemsForDay = trip.items.filter((item) => item.day === activeDay).sort((a, b) => a.position - b.position);
  const shareUrl = trip.share_token ? `${window.location.origin}/shared/${trip.share_token}` : null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-6 md:px-8 md:py-10">
      <header className="mb-4">
        <h1 className="font-heading text-2xl font-bold">{trip.title}</h1>
        <p className="mt-1 text-sm text-ink/60">
          {trip.start_date} &rarr; {trip.end_date} &middot; {trip.currency}
        </p>
      </header>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {trip.share_token ? (
          <>
            <Button
              variant="secondary"
              onClick={() => {
                navigator.clipboard?.writeText(shareUrl ?? "");
                setCopiedLink(true);
                setTimeout(() => setCopiedLink(false), 2000);
              }}
            >
              <LinkIcon size={16} aria-hidden="true" />
              {copiedLink ? "Link copied!" : "Copy share link"}
            </Button>
            <Button variant="ghost" onClick={() => revokeShareMutation.mutate()}>
              Revoke sharing
            </Button>
          </>
        ) : (
          <Button variant="secondary" onClick={() => shareMutation.mutate()} disabled={shareMutation.isPending}>
            <Share2 size={16} aria-hidden="true" />
            Create share link
          </Button>
        )}
      </div>

      <div className="mb-4 flex gap-2 overflow-x-auto" role="tablist" aria-label="Trip days">
        {days.map((day) => (
          <button
            key={day}
            role="tab"
            aria-selected={activeDay === day}
            onClick={() => setActiveDay(day)}
            className={clsx(
              "shrink-0 rounded-full border px-4 py-1.5 text-sm font-medium",
              activeDay === day ? "border-primary bg-primary text-white" : "border-border bg-surface text-ink/70",
            )}
          >
            Day {day}
          </button>
        ))}
      </div>

      {itemsForDay.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border py-8 text-center text-sm text-ink/60">
          No stops on day {activeDay} yet. Add a destination below.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {itemsForDay.map((item, index) => (
            <Card key={item.id} className="flex items-center gap-3 p-3">
              <img
                src={item.destination_snapshot.image.primary}
                alt=""
                className="h-16 w-16 shrink-0 rounded-lg object-cover"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium">{item.destination_snapshot.name}</p>
                {item.notes ? <p className="truncate text-xs text-ink/60">{item.notes}</p> : null}
                {item.estimated_cost != null ? (
                  <p className="text-xs text-ink/60">Est. {item.estimated_cost} {trip.currency}</p>
                ) : null}
              </div>
              <div className="flex shrink-0 flex-col gap-1">
                <button
                  type="button"
                  aria-label="Move up"
                  disabled={index === 0}
                  onClick={() => moveMutation.mutate({ itemId: item.id, direction: "up" })}
                  className="rounded p-1 text-ink/50 hover:bg-canvas disabled:opacity-30"
                >
                  <ArrowUp size={16} />
                </button>
                <button
                  type="button"
                  aria-label="Move down"
                  disabled={index === itemsForDay.length - 1}
                  onClick={() => moveMutation.mutate({ itemId: item.id, direction: "down" })}
                  className="rounded p-1 text-ink/50 hover:bg-canvas disabled:opacity-30"
                >
                  <ArrowDown size={16} />
                </button>
              </div>
              <button
                type="button"
                aria-label="Remove stop"
                onClick={() => deleteItemMutation.mutate(item.id)}
                className="shrink-0 rounded p-1 text-ink/40 hover:text-coral"
              >
                <Trash2 size={16} />
              </button>
            </Card>
          ))}
        </ol>
      )}

      <Card className="mt-4 flex flex-wrap items-end gap-3 p-4">
        <label className="flex min-w-[10rem] flex-1 flex-col gap-1 text-xs font-medium text-ink/70">
          Add a stop to day {activeDay}
          <select
            value={newStopDestinationId}
            onChange={(event) => setNewStopDestinationId(event.target.value)}
            className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
          >
            <option value="">Select a destination...</option>
            {destinationsQuery.data?.items.map((destination) => (
              <option key={destination.id} value={destination.id}>
                {destination.name}
              </option>
            ))}
          </select>
        </label>
        <Button disabled={!newStopDestinationId || addItemMutation.isPending} onClick={() => addItemMutation.mutate()}>
          <Plus size={16} aria-hidden="true" />
          Add stop
        </Button>
        {addItemMutation.isError ? <p className="w-full text-xs text-coral">{errorMessage(addItemMutation.error)}</p> : null}
      </Card>
    </div>
  );
}
