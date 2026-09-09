import { createContext, useContext, useMemo, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as authApi from "@/lib/api/auth";
import { getMe } from "@/lib/api/profile";
import { ApiError } from "@/lib/api/client";
import type { UserProfile } from "@/lib/api/types";

interface AuthContextValue {
  user: UserProfile | null;
  isLoading: boolean;
  login: (input: { email: string; password: string }) => Promise<void>;
  register: (input: { email: string; password: string; display_name: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: getMe,
    retry: false,
    // A 401 just means "not logged in" -- not an error worth surfacing.
    throwOnError: (error) => !(error instanceof ApiError && error.status === 401),
  });

  const invalidateMe = () => queryClient.invalidateQueries({ queryKey: ["me"] });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: invalidateMe,
  });
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: invalidateMe,
  });
  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(["me"], null);
      queryClient.clear();
    },
  });

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.data ?? null,
      isLoading: meQuery.isLoading,
      login: async (input) => {
        await loginMutation.mutateAsync(input);
      },
      register: async (input) => {
        await registerMutation.mutateAsync(input);
      },
      logout: async () => {
        await logoutMutation.mutateAsync();
      },
    }),
    [meQuery.data, meQuery.isLoading, loginMutation, registerMutation, logoutMutation],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
