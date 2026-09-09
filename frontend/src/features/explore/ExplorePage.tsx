import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import * as destinationsApi from "@/lib/api/destinations";
import { DestinationCard } from "@/features/destinations/DestinationCard";
import { useFavourites } from "@/features/destinations/useFavourites";
import { Spinner } from "@/components/ui/Spinner";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { errorMessage } from "@/lib/api/errorMessage";
import clsx from "clsx";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "heritage", label: "Heritage" },
  { value: "nature", label: "Nature" },
  { value: "recreation", label: "Recreation" },
  { value: "stay", label: "Stay" },
  { value: "food", label: "Food" },
  { value: "sport", label: "Sport" },
];

export function ExplorePage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const { isFavourite, toggleFavourite } = useFavourites();

  const recommendationsQuery = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => destinationsApi.getRecommendations(6),
  });

  const destinationsQuery = useQuery({
    queryKey: ["destinations", query, category],
    queryFn: () => destinationsApi.listDestinations({ q: query || undefined, category: category || undefined, limit: 40 }),
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 md:px-8 md:py-10">
      <header className="mb-6">
        <h1 className="font-heading text-2xl font-bold md:text-3xl">Explore Yaoundé</h1>
        <p className="mt-1 text-sm text-ink/60">
          Discover heritage sites, nature spots, and places to stay and eat around the city.
        </p>
      </header>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink/40" size={18} />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search destinations..."
            className="w-full rounded-lg border border-border bg-surface py-2.5 pl-10 pr-3 text-sm focus:border-primary focus:outline-none"
          />
        </label>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
          {CATEGORIES.map((item) => (
            <button
              key={item.value}
              type="button"
              onClick={() => setCategory(item.value)}
              className={clsx(
                "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                category === item.value
                  ? "border-primary bg-primary text-white"
                  : "border-border bg-surface text-ink/70 hover:border-primary/50",
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {recommendationsQuery.data && recommendationsQuery.data.items.length > 0 ? (
        <section className="mb-8">
          <h2 className="mb-3 font-heading text-lg font-semibold">
            {recommendationsQuery.data.personalized ? "Recommended for you" : "Popular in Yaoundé"}
          </h2>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {recommendationsQuery.data.items.map(({ destination, reason }) => (
              <div key={destination.id} className="w-56 shrink-0">
                <DestinationCard
                  destination={destination}
                  isFavourite={isFavourite(destination.id)}
                  onToggleFavourite={(d) => toggleFavourite(d.id)}
                />
                <p className="mt-1 px-1 text-[11px] text-ink/50">{reason}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section>
        {destinationsQuery.isLoading ? <Spinner label="Loading destinations..." /> : null}
        {destinationsQuery.isError ? (
          <ErrorState message={errorMessage(destinationsQuery.error)} onRetry={() => destinationsQuery.refetch()} />
        ) : null}
        {destinationsQuery.data && destinationsQuery.data.items.length === 0 ? (
          <EmptyState title="No destinations found" description="Try a different search term or category." />
        ) : null}
        {destinationsQuery.data && destinationsQuery.data.items.length > 0 ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {destinationsQuery.data.items.map((destination) => (
              <DestinationCard
                key={destination.id}
                destination={destination}
                isFavourite={isFavourite(destination.id)}
                onToggleFavourite={(d) => toggleFavourite(d.id)}
              />
            ))}
          </div>
        ) : null}
      </section>
    </div>
  );
}
