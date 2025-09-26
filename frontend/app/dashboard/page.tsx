"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function DashboardPage() {
  const [sessionInfo, setSessionInfo] = useState({
    username: "",
    sessionId: "",
    expiresAt: "",
  });

  useEffect(() => {
    // Get session info from localStorage
    const sessionId = localStorage.getItem("session_id") || "";
    const expiresAt = localStorage.getItem("expires_at") || "";
    // Note: In a real app, you'd get username from the token or an API call
    setSessionInfo({
      username: "Researcher",
      sessionId,
      expiresAt,
    });
  }, []);

  const cards = [
    {
      title: "AI Chat",
      description: "Interact with the LLM using your documents",
      href: "/chat",
      icon: "💬",
      action: "Start Chat",
    },
    {
      title: "Export Data",
      description: "Export all your research data before session ends",
      href: "#",
      icon: "💾",
      action: "Export All",
      onClick: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        try {
          const response = await fetch("http://localhost:8000/api/export/all", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const data = await response.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], {
              type: "application/json",
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `legal-ai-research-export-${new Date().toISOString()}.json`;
            a.click();
          }
        } catch (error) {
          console.error("Export failed:", error);
          alert("Failed to export data. Please try again.");
        }
      },
    },
  ];

  return (
    <div className="px-4 py-5 sm:px-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">
          Welcome to Your Research Session
        </h2>
      </div>

      {/* Important Notice */}
      <div className="mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Important Reminders
            </h3>
            <div className="mt-2 text-sm text-yellow-700">
              <ul className="list-disc list-inside space-y-1">
                <li>
                  All data is stored in memory only - nothing is saved to disk
                </li>
                <li>
                  Your session will automatically terminate after 72 hours
                </li>
                <li>Export your data before session expiration</li>
                <li>Once terminated, all data is permanently destroyed</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((card) => (
          <div
            key={card.title}
            className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow"
          >
            <div className="px-4 py-5 sm:p-6">
              <div className="text-3xl mb-3">{card.icon}</div>
              <h3 className="text-lg font-medium text-gray-900">
                {card.title}
              </h3>
              <p className="mt-1 text-sm text-gray-500">{card.description}</p>
              {card.onClick ? (
                <button
                  onClick={card.onClick}
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  {card.action}
                </button>
              ) : (
                <Link
                  href={card.href}
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  {card.action}
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
