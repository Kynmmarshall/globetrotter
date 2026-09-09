import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Share2 } from "lucide-react";
import * as itinerariesApi from "@/lib/api/itineraries";
import * as destinationsApi from "@/lib/api/destinations";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { errorMessage } from "@/lib/api/errorMessage";

const tripSchema = z
  .object({
    title: z.string().min(1, "Title is required").max(150),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
    destination_id: z.string().min(1, "Choose a destination to start your trip."),
  })
  .refine((data) => data.end_date >= data.start_date, {
    message: "End date must not be before the start date.",
    path: ["end_date"],
  });

type TripFormValues = z.infer<typeof tripSchema>;

export function TripsListPage() {
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const tripsQuery = useQuery({ queryKey: ["itineraries"], queryFn: itinerariesApi.listItineraries });
  const destinationsQuery = useQuery({
    queryKey: ["destinations", "picker"],
    queryFn: () => destinationsApi.listDestinations({ limit: 100 }),
    enabled: showForm,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TripFormValues>({ resolver: zodResolver(tripSchema) });

  const createMutation = useMutation({
    mutationFn: async (values: TripFormValues) => {
      const trip = await itinerariesApi.createItinerary({
        title: values.title,
        start_date: values.start_date,
        end_date: values.end_date,
      });
      await itinerariesApi.addItineraryItem(trip.id, { destination_id: values.destination_id, day: 1 });
      return trip;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["itineraries"] });
      reset();
      setShowForm(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: itinerariesApi.deleteItinerary,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["itineraries"] }),
  });

  return (
    <div className="mx-auto max-w-4xl px-4 py-6 md:px-8 md:py-10">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-bold">My Trips</h1>
          <p className="mt-1 text-sm text-ink/60">Plan multi-day trips and organize your stops by day.</p>
        </div>
        <Button onClick={() => setShowForm((value) => !value)}>
          <Plus size={16} aria-hidden="true" />
          New trip
        </Button>
      </header>

      {showForm ? (
        <Card className="mb-6 p-4">
          <form
            onSubmit={handleSubmit((values) => createMutation.mutate(values))}
            className="grid grid-cols-1 gap-3 sm:grid-cols-3"
          >
            <label className="flex flex-col gap-1 text-xs font-medium text-ink/70 sm:col-span-3">
              Title
              <input
                {...register("title")}
                placeholder="Yaoundé weekend"
                className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
              />
              {errors.title ? <span className="text-coral">{errors.title.message}</span> : null}
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-ink/70 sm:col-span-3">
              First destination
              <select
                {...register("destination_id")}
                defaultValue=""
                className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
              >
                <option value="" disabled>
                  Select a destination...
                </option>
                {destinationsQuery.data?.items.map((destination) => (
                  <option key={destination.id} value={destination.id}>
                    {destination.name}
                  </option>
                ))}
              </select>
              {errors.destination_id ? <span className="text-coral">{errors.destination_id.message}</span> : null}
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
              Start date
              <input type="date" {...register("start_date")} className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm" />
              {errors.start_date ? <span className="text-coral">{errors.start_date.message}</span> : null}
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
              End date
              <input type="date" {...register("end_date")} className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm" />
              {errors.end_date ? <span className="text-coral">{errors.end_date.message}</span> : null}
            </label>
            <div className="flex items-end">
              <Button type="submit" disabled={isSubmitting || createMutation.isPending}>
                Create trip
              </Button>
            </div>
            {createMutation.isError ? (
              <p className="text-xs text-coral sm:col-span-3">{errorMessage(createMutation.error)}</p>
            ) : null}
          </form>
        </Card>
      ) : null}

      {tripsQuery.isLoading ? <Spinner label="Loading your trips..." /> : null}
      {tripsQuery.isError ? <ErrorState message={errorMessage(tripsQuery.error)} onRetry={() => tripsQuery.refetch()} /> : null}
      {tripsQuery.data && tripsQuery.data.length === 0 ? (
        <EmptyState title="No trips yet" description="Create your first trip to start adding destinations." />
      ) : null}

      {tripsQuery.data && tripsQuery.data.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {tripsQuery.data.map((trip) => (
            <Link key={trip.id} to={`/trips/${trip.id}`} className="group block">
              <Card className="flex h-full flex-col gap-2 p-4 transition-shadow hover:shadow-md">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-heading text-base font-semibold group-hover:underline">{trip.title}</span>
                  <div className="flex gap-1">
                    {trip.is_shared ? <Share2 size={16} className="text-primary" aria-label="Shared" /> : null}
                    <button
                      type="button"
                      aria-label="Delete trip"
                      onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        deleteMutation.mutate(trip.id);
                      }}
                      className="text-ink/40 hover:text-coral"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-ink/60">
                  {trip.start_date} &rarr; {trip.end_date}
                </p>
                <p className="text-xs text-ink/60">
                  {trip.item_count} stop{trip.item_count === 1 ? "" : "s"} &middot; {trip.currency}
                </p>
              </Card>
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}
