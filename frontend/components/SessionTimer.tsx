"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Clock, AlertTriangle } from "lucide-react";

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
      <Clock className="w-4 h-4" />
      <span className="text-sm font-medium">{timeRemaining}</span>
      {warning === "critical" && (
        <AlertTriangle className="w-4 h-4 text-red-600" />
      )}
    </div>
  );
}