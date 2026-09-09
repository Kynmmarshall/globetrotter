import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/app/queryClient";
import { AuthProvider } from "@/features/auth/AuthContext";
import { ProtectedRoute } from "@/features/auth/ProtectedRoute";
import { AppShell } from "@/app/AppShell";
import { AnimatedBackground } from "@/components/ui/AnimatedBackground";
import { ExplorePage } from "@/features/explore/ExplorePage";
import { DestinationDetailPage } from "@/features/destinations/DestinationDetailPage";
import { MapPage } from "@/features/map/MapPage";
import { TripsListPage } from "@/features/itineraries/TripsListPage";
import { TripPlannerPage } from "@/features/itineraries/TripPlannerPage";
import { PublicTripPage } from "@/features/itineraries/PublicTripPage";
import { ProfilePage } from "@/features/profile/ProfilePage";
import { ChatPage } from "@/features/chat/ChatPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AnimatedBackground />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/shared/:token" element={<PublicTripPage />} />

            <Route element={<AppShell />}>
              <Route index element={<ExplorePage />} />
              <Route path="destinations/:id" element={<DestinationDetailPage />} />
              <Route path="map" element={<MapPage />} />

              <Route element={<ProtectedRoute />}>
                <Route path="trips" element={<TripsListPage />} />
                <Route path="trips/:id" element={<TripPlannerPage />} />
                <Route path="chat" element={<ChatPage />} />
                <Route path="profile" element={<ProfilePage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
