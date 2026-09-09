import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as profileApi from "@/lib/api/profile";
import { useAuth } from "@/features/auth/AuthContext";

export function useFavourites() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const favouritesQuery = useQuery({
    queryKey: ["favourites"],
    queryFn: profileApi.listFavourites,
    enabled: Boolean(user),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["favourites"] });
    queryClient.invalidateQueries({ queryKey: ["me"] });
  };

  const addMutation = useMutation({ mutationFn: profileApi.addFavourite, onSuccess: invalidate });
  const removeMutation = useMutation({ mutationFn: profileApi.removeFavourite, onSuccess: invalidate });

  const favouriteIds = new Set((favouritesQuery.data ?? []).map((f) => f.destination_id));

  return {
    favouriteIds,
    isFavourite: (destinationId: string) => favouriteIds.has(destinationId),
    toggleFavourite: (destinationId: string) => {
      if (favouriteIds.has(destinationId)) {
        removeMutation.mutate(destinationId);
      } else {
        addMutation.mutate(destinationId);
      }
    },
  };
}
