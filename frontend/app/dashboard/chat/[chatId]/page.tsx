"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { useChatHistory, useSendMessage, useUploadDocument } from "@/lib/hooks";
import type { Conversation, Message } from "@/types";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Paperclip } from "lucide-react";

function ChatConversation() {
  const params = useParams();
  const chatId = params.chatId as string;
  const [message, setMessage] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { data: conversations = [], isLoading } = useChatHistory();
  const sendMessageMutation = useSendMessage();
  const uploadMutation = useUploadDocument();

  const currentConversation = conversations.find(
    (c: Conversation) => c.conversation_id === chatId
  );

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages]);

  // Auto-resize textarea when message changes
  useEffect(() => {
    if (textareaRef.current) {
      // Reset height to auto to get accurate scrollHeight
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.overflowY = 'hidden';

      const scrollHeight = textareaRef.current.scrollHeight;

      if (scrollHeight > 128) {
        // Content exceeds max height - set to max and show scrollbar
        textareaRef.current.style.height = '128px';
        textareaRef.current.style.overflowY = 'auto';
      } else {
        // Content fits - set to actual height and hide scrollbar
        textareaRef.current.style.height = scrollHeight + 'px';
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  }, [message]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async (): Promise<string[]> => {
    if (selectedFiles.length === 0) return [];

    setIsUploading(true);
    const docIds: string[] = [];

    try {
      for (const file of selectedFiles) {
        const result = await uploadMutation.mutateAsync(file);
        docIds.push(result.document_id);
      }
      return docIds;
    } catch (error) {
      console.error("Failed to upload files:", error);
      throw error;
    } finally {
      setIsUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      (!message.trim() && selectedFiles.length === 0) ||
      sendMessageMutation.isPending ||
      isUploading
    )
      return;

    let documentIds: string[] = [];

    // Upload files first if any are selected
    if (selectedFiles.length > 0) {
      try {
        documentIds = await uploadFiles();
      } catch (e) {
        console.error("Failed to upload files:", e);
        alert("Failed to upload files. Please try again.");
        return;
      }
    }

    const messageToSend = message || "[Files attached]";
    setMessage("");
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    sendMessageMutation.mutate(
      { message: messageToSend, conversationId: chatId, documentIds },
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
          href="/dashboard/chat/history"
          className="text-gray-700 hover:text-gray-900"
        >
          ← Back to History
        </Link>
      </div>
    );
  }

  const messages = currentConversation.messages || [];

  return (
    <div className="flex flex-col h-full">
      {/* Messages - with bottom padding to account for fixed input */}
      <div className="flex-1 overflow-y-auto p-4 pb-32 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No messages yet in this conversation
          </div>
        ) : (
          messages.map((msg: Message, index: number) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg ${
                  msg.role === "user"
                    ? "bg-gray-900 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {/* Display attached documents if any */}
                {msg.document_contents &&
                  Object.keys(msg.document_contents).length > 0 && (
                    <div
                      className={`mb-2 pb-2 border-b ${
                        msg.role === "user"
                          ? "border-gray-700"
                          : "border-gray-300"
                      }`}
                    >
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(msg.document_contents).map(
                          ([docId, docData]) => (
                            <span
                              key={docId}
                              className={`inline-flex items-center px-2 py-1 rounded text-xs ${
                                msg.role === "user"
                                  ? "bg-gray-800 text-gray-200"
                                  : "bg-gray-200 text-gray-700"
                              }`}
                              title={`${docData.word_count || 0} words`}
                            >
                              📎 {docData.filename}
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p
                  className={`text-xs mt-2 ${
                    msg.role === "user" ? "text-gray-400" : "text-gray-500"
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
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display - positioned above the fixed input */}
      {sendMessageMutation.error && (
        <div className="fixed bottom-20 left-16 right-0 z-20 px-4 py-2 bg-red-50 border-t border-red-200">
          <div className="max-w-4xl mx-auto">
            <p className="text-sm text-red-800">
              {sendMessageMutation.error instanceof Error
                ? sendMessageMutation.error.message
                : "Failed to send message"}
            </p>
          </div>
        </div>
      )}

      {/* Fixed Input Area at bottom of viewport */}
      <form onSubmit={handleSubmit} className="fixed bottom-0 left-16 right-0 bg-white border-t p-4 z-30">
        <div className="max-w-4xl mx-auto">
          {/* Selected Files Display */}
          {selectedFiles.length > 0 && (
            <div className="mb-2 p-2 bg-gray-50 rounded-md">
              <div className="flex flex-wrap gap-2">
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="inline-flex items-center px-3 py-1 bg-white border border-gray-300 rounded-md text-sm text-gray-700"
                  >
                    <span className="mr-1">📄</span>
                    <span className="mr-2">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="text-gray-500 hover:text-red-500"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              {isUploading && (
                <div className="mt-2 text-sm text-gray-500">
                  Uploading files...
                </div>
              )}
            </div>
          )}

          <div className="flex items-end space-x-2">
          {/* File Input Button */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            accept=".pdf,.txt,.docx"
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-flex items-center px-3 h-[42px] border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer flex-shrink-0"
          >
            <Paperclip className="w-5 h-5 text-gray-500" />
          </label>

          {/* Message Input - Auto-expanding textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              // Submit on Enter (without shift)
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as any);
              }
            }}
            placeholder="Type your message..."
            disabled={sendMessageMutation.isPending || isUploading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 disabled:opacity-50 text-gray-900 resize-none leading-normal"
            rows={1}
            style={{
              maxHeight: '128px',
            }}
            autoFocus
          />

            {/* Send Button */}
            <button
              type="submit"
              disabled={
                sendMessageMutation.isPending ||
                isUploading ||
                (!message.trim() && selectedFiles.length === 0)
              }
              className="px-6 h-[42px] bg-gray-900 text-white rounded-md hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer flex-shrink-0"
            >
              {sendMessageMutation.isPending || isUploading ? "..." : "Send"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <div className="h-full max-w-4xl mx-auto">
        <ChatConversation />
      </div>
    </ProtectedRoute>
  );
}
