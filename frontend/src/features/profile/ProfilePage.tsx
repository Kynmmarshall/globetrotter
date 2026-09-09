import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import * as profileApi from "@/lib/api/profile";
import * as itinerariesApi from "@/lib/api/itineraries";
import { useAuth } from "@/features/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { errorMessage } from "@/lib/api/errorMessage";
import type { Preferences } from "@/lib/api/types";

interface ProfileFormValues {
  display_name: string;
  bio: string;
  home_city: string;
}

const INTEREST_OPTIONS = ["nature", "heritage", "food", "sport", "recreation", "stay"];
const BUDGET_OPTIONS: NonNullable<Preferences["budget_band"]>[] = ["low", "medium", "high"];
const PACE_OPTIONS: NonNullable<Preferences["pace"]>[] = ["relaxed", "balanced", "packed"];

export function ProfilePage() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [interests, setInterests] = useState<string[]>([]);
  const [budgetBand, setBudgetBand] = useState<Preferences["budget_band"]>(null);
  const [pace, setPace] = useState<Preferences["pace"]>(null);

  const tripsQuery = useQuery({ queryKey: ["itineraries"], queryFn: itinerariesApi.listItineraries, enabled: Boolean(user) });
  const favouritesQuery = useQuery({
    queryKey: ["favourites"],
    queryFn: profileApi.listFavourites,
    enabled: Boolean(user),
  });

  const { register, handleSubmit } = useForm<ProfileFormValues>({
    values: user ? { display_name: user.display_name, bio: user.bio ?? "", home_city: user.home_city ?? "" } : undefined,
  });

  useEffect(() => {
    if (user) {
      setInterests(user.preferences.interests);
      setBudgetBand(user.preferences.budget_band);
      setPace(user.preferences.pace);
    }
  }, [user]);

  const updateProfileMutation = useMutation({
    mutationFn: profileApi.updateProfile,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });

  const updatePreferencesMutation = useMutation({
    mutationFn: profileApi.updatePreferences,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["me"] }),
  });

  const removeFavouriteMutation = useMutation({
    mutationFn: profileApi.removeFavourite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favourites"] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  if (!user) {
    return <Spinner label="Loading profile..." />;
  }

  const toggleInterest = (interest: string) => {
    setInterests((current) =>
      current.includes(interest) ? current.filter((item) => item !== interest) : [...current, interest],
    );
  };

  const savePreferences = () => {
    updatePreferencesMutation.mutate({
      interests,
      budget_band: budgetBand,
      pace,
      accessibility_needs: user.preferences.accessibility_needs,
      starting_area: user.preferences.starting_area,
    });
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 md:px-8 md:py-10">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-heading text-2xl font-bold">Your profile</h1>
          <p className="mt-1 text-sm text-ink/60">{user.email}</p>
        </div>
        <Button variant="secondary" onClick={() => logout()}>
          Log out
        </Button>
      </header>

      <div className="mb-4 flex gap-4 text-sm text-ink/70">
        <span>{user.favourite_count} favourites</span>
        <span>{tripsQuery.data?.length ?? 0} trips</span>
      </div>

      <Card className="mb-6 p-4">
        <h2 className="mb-3 font-heading text-sm font-semibold">Profile details</h2>
        <form
          onSubmit={handleSubmit((values) => updateProfileMutation.mutate(values))}
          className="flex flex-col gap-3"
        >
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Display name
            <input {...register("display_name")} className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm" />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Home city
            <input {...register("home_city")} className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm" />
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Bio
            <textarea
              {...register("bio")}
              rows={3}
              className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
            />
          </label>
          <Button type="submit" disabled={updateProfileMutation.isPending} className="self-start">
            Save profile
          </Button>
          {updateProfileMutation.isError ? (
            <p className="text-xs text-coral">{errorMessage(updateProfileMutation.error)}</p>
          ) : null}
        </form>
      </Card>

      <Card className="mb-6 p-4">
        <h2 className="mb-3 font-heading text-sm font-semibold">Travel preferences</h2>
        <p className="mb-2 text-xs font-medium text-ink/60">Interests</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {INTEREST_OPTIONS.map((interest) => (
            <button
              key={interest}
              type="button"
              onClick={() => toggleInterest(interest)}
              className={
                interests.includes(interest)
                  ? "rounded-full bg-primary px-3 py-1 text-xs font-medium text-white"
                  : "rounded-full border border-border px-3 py-1 text-xs font-medium text-ink/70"
              }
            >
              {interest}
            </button>
          ))}
        </div>
        <div className="mb-4 flex gap-4">
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Budget
            <select
              value={budgetBand ?? ""}
              onChange={(event) => setBudgetBand((event.target.value || null) as Preferences["budget_band"])}
              className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
            >
              <option value="">Not set</option>
              {BUDGET_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-medium text-ink/70">
            Pace
            <select
              value={pace ?? ""}
              onChange={(event) => setPace((event.target.value || null) as Preferences["pace"])}
              className="rounded-lg border border-border bg-canvas px-3 py-2 text-sm"
            >
              <option value="">Not set</option>
              {PACE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <Button onClick={savePreferences} disabled={updatePreferencesMutation.isPending}>
          Save preferences
        </Button>
      </Card>

      <Card className="p-4">
        <h2 className="mb-3 font-heading text-sm font-semibold">Favourites</h2>
        {favouritesQuery.data && favouritesQuery.data.length === 0 ? (
          <p className="text-sm text-ink/60">No favourites saved yet.</p>
        ) : null}
        <ul className="flex flex-col gap-2">
          {favouritesQuery.data?.map((favourite) => (
            <li key={favourite.destination_id} className="flex items-center justify-between text-sm">
              <span>{favourite.destination_id}</span>
              <button
                type="button"
                onClick={() => removeFavouriteMutation.mutate(favourite.destination_id)}
                className="text-xs font-medium text-coral"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
