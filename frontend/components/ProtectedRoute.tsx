"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, checkAuth } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Mark as hydrated to prevent SSR mismatches
    setIsHydrated(true);

    // Check authentication
    const authenticated = checkAuth();
    if (!authenticated) {
      router.push("/login");
    } else {
      // Small delay to ensure auth context is fully ready
      setTimeout(() => setIsLoading(false), 100);
    }
  }, [checkAuth, router]);

  // Don't render until hydrated to prevent SSR issues
  if (!isHydrated) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Verifying session...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}