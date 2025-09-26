"use client";

import { useChatHistory } from "@/lib/hooks";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ProtectedRoute from "@/components/ProtectedRoute";
import type { Conversation } from "@/types";

function ChatHistoryList() {
  const { data: conversations = [], isLoading, error, isError } = useChatHistory() as {
    data: Conversation[] | undefined;
    isLoading: boolean;
    error: any;
    isError: boolean;
  };
  const router = useRouter();

  // Add console log for debugging
  console.log("ChatHistory Debug:", {
    conversations,
    isLoading,
    error,
    isError,
    hasToken: !!localStorage.getItem("access_token")
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-gray-500">Loading conversations...</div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 mb-4">Failed to load conversations</div>
        <p className="text-sm text-gray-600 mb-4">
          {error?.message || "An error occurred while fetching chat history"}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="mt-2 text-sm text-gray-600">No conversations yet</p>
        <Link
          href="/chat"
          className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Start Your First Conversation
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {conversations.map((conversation: Conversation) => (
        <div
          key={conversation.conversation_id}
          onClick={() => router.push(`/chat/${conversation.conversation_id}`)}
          className="p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md hover:border-gray-300 cursor-pointer transition-all"
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <p className="text-gray-900 font-medium">
                {conversation.messages && conversation.messages.length > 0
                  ? conversation.messages[0].content.substring(0, 100) +
                    (conversation.messages[0].content.length > 100 ? "..." : "")
                  : "Empty conversation"}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {conversation.messages?.length || 0} messages
              </p>
            </div>
            <div className="text-sm text-gray-400">
              {new Date(conversation.created_at).toLocaleDateString()}
              <br />
              {new Date(conversation.created_at).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ChatHistoryPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Conversation History</h1>
          <Link
            href="/chat"
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            New Conversation
          </Link>
        </div>

        <ChatHistoryList />
      </div>
    </ProtectedRoute>
  );
}