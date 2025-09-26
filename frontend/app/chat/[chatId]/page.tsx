"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useChatHistory, useSendMessage } from "@/lib/hooks";
import ProtectedRoute from "@/components/ProtectedRoute";
import type { Message } from "@/types";

function ChatConversation() {
  const params = useParams();
  const router = useRouter();
  const chatId = params.chatId as string;
  const [message, setMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: conversations = [], isLoading } = useChatHistory();
  const sendMessageMutation = useSendMessage();

  const currentConversation = conversations.find(
    (c: any) => c.conversation_id === chatId
  );

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMessageMutation.isPending) return;

    const messageToSend = message;
    setMessage("");

    sendMessageMutation.mutate(
      { message: messageToSend, conversationId: chatId },
      {
        onSuccess: () => {
          scrollToBottom();
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <div className="text-gray-500">Loading conversation...</div>
      </div>
    );
  }

  if (!currentConversation) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 mb-4">Conversation not found</p>
        <Link
          href="/chat/history"
          className="text-indigo-600 hover:text-indigo-800"
        >
          ← Back to History
        </Link>
      </div>
    );
  }

  const messages = currentConversation.messages || [];

  return (
    <div className="flex flex-col h-[calc(100vh-200px)]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <Link
          href="/chat/history"
          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
        >
          ← Back to History
        </Link>
        <Link
          href="/chat"
          className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700"
        >
          New Chat
        </Link>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No messages yet in this conversation
          </div>
        ) : (
          messages.map((msg: Message, index: number) => (
            <div
              key={index}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p
                  className={`text-xs mt-2 ${
                    msg.role === "user" ? "text-indigo-200" : "text-gray-500"
                  }`}
                >
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}

        {sendMessageMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-3 rounded-lg">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {sendMessageMutation.error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200">
          <p className="text-sm text-red-800">
            {sendMessageMutation.error instanceof Error
              ? sendMessageMutation.error.message
              : "Failed to send message"}
          </p>
        </div>
      )}

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={sendMessageMutation.isPending}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
            autoFocus
          />
          <button
            type="submit"
            disabled={sendMessageMutation.isPending || !message.trim()}
            className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sendMessageMutation.isPending ? "..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <div className="max-w-4xl mx-auto">
        <ChatConversation />
      </div>
    </ProtectedRoute>
  );
}