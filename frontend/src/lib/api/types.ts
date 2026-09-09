/** TypeScript shapes mirroring the backend Pydantic response schemas.
 *
 * Kept hand-written (not generated) for now; if the API surface grows much
 * further, generate these from each service's OpenAPI schema instead of
 * maintaining them by hand.
 */

export interface ImageVariant {
  width: number;
  height: number;
  path: string;
}

export interface DestinationImage {
  alt: string;
  primary: string;
  variants: ImageVariant[];
}

export interface Destination {
  id: string;
  slug: string;
  name: string;
  category: string;
  lat: number;
  lng: number;
  tags: string[];
  description: string;
  city: string;
  country: string;
  currency: string;
  timezone: string;
  image: DestinationImage;
}

export interface DestinationListResponse {
  items: Destination[];
  total: number;
  limit: number;
  offset: number;
}

export interface RecommendationItem {
  destination: Destination;
  reason: string;
}

export interface RecommendationListResponse {
  items: RecommendationItem[];
  personalized: boolean;
}

export interface RouteStep {
  instruction: string;
  distance_meters: number;
  duration_seconds: number;
}

export interface DirectionsResponse {
  profile: "driving";
  distance_meters: number;
  duration_seconds: number;
  geometry: [number, number][];
  steps: RouteStep[];
}

export type DirectionsWaypoint = { lat: number; lng: number } | { destination_id: string };

export interface Preferences {
  interests: string[];
  budget_band: "low" | "medium" | "high" | null;
  pace: "relaxed" | "balanced" | "packed" | null;
  accessibility_needs: string[];
  starting_area: string | null;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  bio: string | null;
  home_city: string | null;
  avatar_url: string | null;
  locale: string;
  preferences: Preferences;
  favourite_count: number;
  created_at: string;
}

export interface FavouriteResponse {
  destination_id: string;
  created_at: string;
}

export interface ItineraryItem {
  id: string;
  destination_id: string;
  day: number;
  position: number;
  scheduled_time: string | null;
  duration_minutes: number | null;
  notes: string | null;
  estimated_cost: number | null;
  destination_snapshot: {
    destination_id: string;
    name: string;
    category: string;
    lat: number;
    lng: number;
    image: DestinationImage;
  };
  created_at: string;
}

export interface Itinerary {
  id: string;
  owner_id: string;
  title: string;
  start_date: string;
  end_date: string;
  currency: string;
  revision: number;
  items: ItineraryItem[];
  share_token: string | null;
  created_at: string;
  updated_at: string;
}

export interface ItinerarySummary {
  id: string;
  title: string;
  start_date: string;
  end_date: string;
  currency: string;
  item_count: number;
  is_shared: boolean;
  created_at: string;
}

export interface ChatMessageResponse {
  id: string;
  room_id: string;
  sequence: number;
  sender_id: string;
  sender_display_name: string;
  text: string;
  created_at: string;
  hidden: boolean;
}

export interface ChatHistoryResponse {
  messages: ChatMessageResponse[];
  next_before_sequence: number | null;
}
