"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function SessionTimer() {
  const router = useRouter();
  const [timeRemaining, setTimeRemaining] = useState<string>("");
  const [warning, setWarning] = useState<string>("");

  useEffect(() => {
    const expiresAt = localStorage.getItem("expires_at");
    if (!expiresAt) {
      router.push("/login");
      return;
    }

    const updateTimer = () => {
      const now = new Date().getTime();
      const expiry = new Date(expiresAt).getTime();
      const remaining = expiry - now;

      if (remaining <= 0) {
        localStorage.clear();
        router.push("/login");
        return;
      }

      const days = Math.floor(remaining / (1000 * 60 * 60 * 24));
      const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));

      setTimeRemaining(`${days}d ${hours}h ${minutes}m`);

      // Set warnings
      const hoursRemaining = remaining / (1000 * 60 * 60);
      if (hoursRemaining <= 1) {
        setWarning("critical");
      } else if (hoursRemaining <= 24) {
        setWarning("warning");
      } else {
        setWarning("");
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [router]);

  const getTimerColor = () => {
    if (warning === "critical") return "text-red-600 border-red-600";
    if (warning === "warning") return "text-yellow-600 border-yellow-600";
    return "text-gray-700 border-gray-300";
  };

  return (
    <div className={`h-10 px-4 flex items-center space-x-2 rounded-lg border-2 ${getTimerColor()}`}>
      <svg
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span className="text-sm font-medium">{timeRemaining}</span>
      {warning === "critical" && (
        <svg
          className="w-4 h-4 text-red-600"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
            clipRule="evenodd"
          />
        </svg>
      )}
    </div>
  );
}