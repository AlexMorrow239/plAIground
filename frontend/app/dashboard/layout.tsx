"use client";

import SessionTimer from "@/components/SessionTimer";
import { useExportData, useExportZip } from "@/lib/hooks";
import {
  ChevronDownIcon,
  ClockIcon,
  DatabaseIcon,
  DownloadIcon,
  FileArchiveIcon,
  HomeIcon,
  LogOutIcon,
  MessageSquareIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const exportMutation = useExportData();
  const exportZipMutation = useExportZip();
  const [showExportMenu, setShowExportMenu] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.clear();
    router.push("/login");
  };

  const handleExportJSON = () => {
    setShowExportMenu(false);
    exportMutation.mutate(undefined, {
      onError: (error) => {
        console.error("Export failed:", error);
        alert("Failed to export data. Please try again.");
      },
    });
  };

  const handleExportZIP = () => {
    setShowExportMenu(false);
    exportZipMutation.mutate(undefined, {
      onError: (error) => {
        console.error("Export failed:", error);
        alert("Failed to export data as ZIP. Please try again.");
      },
    });
  };

  const navItems = [
    {
      href: "/dashboard",
      label: "Dashboard",
      icon: <HomeIcon className="w-6 h-6" />,
    },
    {
      href: "/dashboard/chat",
      label: "Chat",
      icon: <MessageSquareIcon className="w-6 h-6" />,
    },
    {
      href: "/dashboard/chat/history",
      label: "History",
      icon: <ClockIcon className="w-6 h-6" />,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Minimal Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-16 bg-gray-900 flex flex-col items-center py-4 shadow-lg z-50">
        {/* Navigation Items */}
        <nav className="flex-1 flex flex-col items-center space-y-4 mt-4">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`w-12 h-12 flex items-center justify-center rounded-lg transition-colors ${
                pathname === item.href
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`}
              title={item.label}
            >
              {item.icon}
            </Link>
          ))}
        </nav>

        {/* Logout Button at Bottom */}
        <button
          onClick={handleLogout}
          className="w-12 h-12 flex items-center justify-center rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          title="Logout"
        >
          <LogOutIcon className="w-6 h-6" />
        </button>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 ml-16 flex flex-col">
        {/* Minimal Top Header */}
        <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="px-6 py-3 flex items-center justify-end space-x-4">
            <SessionTimer />

            {/* Export dropdown menu */}
            <div className="relative">
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                disabled={
                  exportMutation.isPending || exportZipMutation.isPending
                }
                className="h-10 bg-gray-900 text-white px-4 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors text-sm font-medium"
              >
                <DownloadIcon className="w-4 h-4" />
                <span>
                  {exportMutation.isPending || exportZipMutation.isPending
                    ? "Exporting..."
                    : "Export"}
                </span>
                <ChevronDownIcon className="w-4 h-4" />
              </button>

              {showExportMenu && (
                <>
                  {/* Backdrop to close menu when clicking outside */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setShowExportMenu(false)}
                  />

                  {/* Dropdown menu */}
                  <div className="absolute right-0 mt-2 w-56 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
                    <div className="py-1">
                      <button
                        onClick={handleExportZIP}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                      >
                        <FileArchiveIcon className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium">Export as ZIP</div>
                          <div className="text-xs text-gray-500">
                            Text files for conversations
                          </div>
                        </div>
                      </button>

                      <button
                        onClick={handleExportJSON}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                      >
                        <DatabaseIcon className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium">Export as JSON</div>
                          <div className="text-xs text-gray-500">
                            Structured data format
                          </div>
                        </div>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="h-10 bg-gray-900 text-white px-4 rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2 transition-colors text-sm font-medium"
            >
              <span>Logout</span>
              <LogOutIcon className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
