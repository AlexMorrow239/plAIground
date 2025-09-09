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
    if (warning === "critical") return "text-red-600 bg-red-100";
    if (warning === "warning") return "text-yellow-600 bg-yellow-100";
    return "text-green-600 bg-green-100";
  };

  return (
    <div className={`px-4 py-2 rounded-lg ${getTimerColor()}`}>
      <div className="text-sm font-medium">Session Time Remaining</div>
      <div className="text-lg font-bold">{timeRemaining}</div>
      {warning === "critical" && (
        <div className="text-xs mt-1">⚠️ Export your data now!</div>
      )}
    </div>
  );
}