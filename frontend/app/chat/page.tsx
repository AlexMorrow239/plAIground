"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSendMessage } from "@/lib/hooks";
import ProtectedRoute from "@/components/ProtectedRoute";

interface ChatResponse {
  conversation_id: string;
  response: string;
  timestamp: string;
}

function NewChatPage() {
  const [message, setMessage] = useState("");
  const router = useRouter();
  const sendMessageMutation = useSendMessage();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMessageMutation.isPending) return;

    sendMessageMutation.mutate(
      { message: message.trim(), conversationId: undefined },
      {
        onSuccess: (data: ChatResponse) => {
          router.push(`/chat/${data.conversation_id}`);
        },
      }
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Start a New Conversation</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
            What would you like to discuss?
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            rows={4}
            disabled={sendMessageMutation.isPending}
            autoFocus
          />
        </div>

        {sendMessageMutation.error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              {sendMessageMutation.error instanceof Error
                ? sendMessageMutation.error.message
                : "Failed to send message"}
            </p>
          </div>
        )}

        <button
          type="submit"
          disabled={sendMessageMutation.isPending || !message.trim()}
          className="w-full px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {sendMessageMutation.isPending ? "Starting conversation..." : "Start Conversation"}
        </button>
      </form>

      <div className="mt-8 text-center">
        <a href="/chat/history" className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
          View Conversation History →
        </a>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <NewChatPage />
    </ProtectedRoute>
  );
}