import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import * as itinerariesApi from "@/lib/api/itineraries";
import { Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/States";
import { Card } from "@/components/ui/Card";
import { errorMessage } from "@/lib/api/errorMessage";

export function PublicTripPage() {
  const { token = "" } = useParams();

  const tripQuery = useQuery({
    queryKey: ["public-itinerary", token],
    queryFn: () => itinerariesApi.getPublicItinerary(token),
  });

  if (tripQuery.isLoading) return <Spinner label="Loading shared trip..." />;
  if (tripQuery.isError || !tripQuery.data) {
    return <ErrorState message={errorMessage(tripQuery.error, "This share link is invalid or has been revoked.")} />;
  }

  const trip = tripQuery.data;
  const days = Array.from(new Set(trip.items.map((item) => item.day))).sort((a, b) => a - b);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">Shared trip</p>
        <h1 className="mt-1 font-heading text-2xl font-bold">{trip.title}</h1>
        <p className="mt-1 text-sm text-ink/60">
          {trip.start_date} &rarr; {trip.end_date}
        </p>
      </header>

      {days.map((day) => (
        <section key={day} className="mb-6">
          <h2 className="mb-2 font-heading text-lg font-semibold">Day {day}</h2>
          <div className="flex flex-col gap-2">
            {trip.items
              .filter((item) => item.day === day)
              .sort((a, b) => a.position - b.position)
              .map((item, index) => (
                <Card key={index} className="flex items-center gap-3 p-3">
                  <img
                    src={item.destination_snapshot.image.primary}
                    alt=""
                    className="h-14 w-14 rounded-lg object-cover"
                  />
                  <div>
                    <p className="font-medium">{item.destination_snapshot.name}</p>
                    {item.scheduled_time ? <p className="text-xs text-ink/60">{item.scheduled_time}</p> : null}
                  </div>
                </Card>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
