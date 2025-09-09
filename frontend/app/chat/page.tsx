"use client";

import { useState, useEffect, useRef } from "react";
import { useChatHistory, useSendMessage, useClearConversation } from "@/lib/hooks";
import type { Message, Conversation } from "@/types"

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: conversations = [], isLoading } = useChatHistory();
  const sendMessageMutation = useSendMessage();
  const clearConversationMutation = useClearConversation();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversations]);

  useEffect(() => {
    if (conversations.length > 0 && !currentConversationId) {
      setCurrentConversationId(conversations[0].conversation_id);
    }
  }, [conversations, currentConversationId]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMessageMutation.isPending) return;

    const userMessage = message;
    setMessage("");

    sendMessageMutation.mutate(
      { message: userMessage, conversationId: currentConversationId || undefined },
      {
        onSuccess: (data) => {
          setCurrentConversationId(data.conversation_id);
        },
      }
    );
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
  };

  const clearConversation = (conversationId: string) => {
    if (!confirm("Are you sure you want to clear this conversation?")) return;

    clearConversationMutation.mutate(conversationId, {
      onSuccess: () => {
        setCurrentConversationId(null);
      },
      onError: (error) => {
        console.error("Failed to clear conversation:", error);
      },
    });
  };

  const currentConversation = conversations.find((c: Conversation) => c.conversation_id === currentConversationId);
  const messages = currentConversation?.messages || [];

  return (
    <div className="flex h-[calc(100vh-200px)]">
      {/* Sidebar - Conversation History */}
      <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
        <button
          onClick={startNewConversation}
          className="w-full mb-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          New Conversation
        </button>
        
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Conversations</h3>
          {isLoading ? (
            <div className="p-2 text-sm text-gray-500">Loading conversations...</div>
          ) : (
            conversations.map((conv: Conversation) => (
            <div
              key={conv.conversation_id}
              className={`p-2 rounded cursor-pointer hover:bg-gray-100 ${
                conv.conversation_id === currentConversationId ? "bg-gray-200" : ""
              }`}
              onClick={() => setCurrentConversationId(conv.conversation_id)}
            >
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-700 truncate flex-1">
                  {conv.messages && conv.messages.length > 0 
                    ? `${conv.messages[0].content.substring(0, 30)}...`
                    : "Empty conversation"
                  }
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    clearConversation(conv.conversation_id);
                  }}
                  className="text-red-500 hover:text-red-700 text-xs ml-2"
                >
                  ✕
                </button>
              </div>
              <div className="text-xs text-gray-500">
                {new Date(conv.created_at).toLocaleString()}
              </div>
            </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
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
              <p className="mt-2 text-sm text-gray-600">
                Start a conversation with the AI assistant
              </p>
              <p className="mt-1 text-xs text-gray-500">
                The AI can reference your uploaded documents
              </p>
            </div>
          ) : (
            messages.map((msg: Message, index: number) => (
              <div
                key={index}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-3xl px-4 py-2 rounded-lg ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className={`text-xs mt-1 ${
                    msg.role === "user" ? "text-indigo-200" : "text-gray-500"
                  }`}>
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
          {sendMessageMutation.isPending && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-2 rounded-lg">
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
        <form onSubmit={sendMessage} className="border-t p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type your message..."
              disabled={sendMessageMutation.isPending}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={sendMessageMutation.isPending || !message.trim()}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sendMessageMutation.isPending ? "Sending..." : "Send"}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Note: The AI has access to your uploaded documents and can reference them in responses.
          </p>
        </form>
      </div>
    </div>
  );
}