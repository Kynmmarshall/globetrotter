import { Link } from "react-router-dom";
import { Heart, MapPin } from "lucide-react";
import clsx from "clsx";
import { Card } from "@/components/ui/Card";
import type { Destination } from "@/lib/api/types";

const CATEGORY_LABELS: Record<string, string> = {
  heritage: "Heritage",
  nature: "Nature",
  recreation: "Recreation",
  stay: "Stay",
  food: "Food",
  sport: "Sport",
};

export function DestinationCard({
  destination,
  isFavourite,
  onToggleFavourite,
}: {
  destination: Destination;
  isFavourite?: boolean;
  onToggleFavourite?: (destination: Destination) => void;
}) {
  return (
    <Link to={`/destinations/${destination.id}`} className="group block">
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <div className="aspect-[4/3] w-full overflow-hidden bg-border/40">
          <img
            src={destination.image.primary}
            alt={destination.image.alt}
            loading="lazy"
            width={destination.image.variants[1]?.width ?? 800}
            height={destination.image.variants[1]?.height ?? 600}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />
        </div>
        <div className="flex flex-col gap-1.5 p-3">
          <div className="flex items-start justify-between gap-2">
            <span className="font-heading text-sm font-semibold group-hover:underline">{destination.name}</span>
            {onToggleFavourite ? (
              <button
                type="button"
                aria-pressed={isFavourite}
                aria-label={isFavourite ? "Remove from favourites" : "Save to favourites"}
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  onToggleFavourite(destination);
                }}
                className="shrink-0 rounded-full p-1.5 text-ink/50 hover:bg-canvas hover:text-coral"
              >
                <Heart size={18} className={clsx(isFavourite && "fill-coral text-coral")} />
              </button>
            ) : null}
          </div>
          <div className="flex items-center gap-1 text-xs text-ink/60">
            <MapPin size={12} aria-hidden="true" />
            {destination.city}
          </div>
          <span className="w-fit rounded-full bg-canvas px-2 py-0.5 text-[11px] font-medium text-ink/70">
            {CATEGORY_LABELS[destination.category] ?? destination.category}
          </span>
        </div>
      </Card>
    </Link>
  );
}
