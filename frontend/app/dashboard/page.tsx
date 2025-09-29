"use client";

import Link from "next/link";

export default function DashboardPage() {
  const cards = [
    {
      title: "AI Chat",
      description:
        "Interact with the LLM and upload documents directly in chat",
      href: "/dashboard/chat",
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
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
                >
                  {card.action}
                </button>
              ) : (
                <Link
                  href={card.href}
                  className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
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
