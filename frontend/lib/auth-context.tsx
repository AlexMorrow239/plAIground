"use client";

import { useRouter } from "next/navigation";
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface AuthContextType {
  isAuthenticated: boolean;
  sessionId: string | null;
  expiresAt: Date | null;
  checkAuth: () => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<Date | null>(null);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("session_id");
    localStorage.removeItem("expires_at");
    setIsAuthenticated(false);
    setSessionId(null);
    setExpiresAt(null);
    router.push("/login");
  }, [router]);

  const checkAuth = useCallback((): boolean => {
    const token = localStorage.getItem("access_token");
    const storedSessionId = localStorage.getItem("session_id");
    const storedExpiresAt = localStorage.getItem("expires_at");

    if (!token || !storedSessionId || !storedExpiresAt) {
      setIsAuthenticated(false);
      return false;
    }

    const expiry = new Date(storedExpiresAt);
    const now = new Date();

    if (expiry <= now) {
      // Token expired
      logout();
      return false;
    }

    setIsAuthenticated(true);
    setSessionId(storedSessionId);
    setExpiresAt(expiry);
    return true;
  }, [logout]);

  useEffect(() => {
    checkAuth();

    // Check auth status every minute
    const interval = setInterval(() => {
      if (!checkAuth()) {
        router.push("/login");
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [checkAuth, router]);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        sessionId,
        expiresAt,
        checkAuth,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
