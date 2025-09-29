"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { useSendMessage, useUploadDocument } from "@/lib/hooks";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

interface ChatResponse {
  conversation_id: string;
  response: string;
  timestamp: string;
}

function NewChatPage() {
  const [message, setMessage] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const sendMessageMutation = useSendMessage();
  const uploadMutation = useUploadDocument();

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
      } catch (error) {
        console.error(error);
        alert("Failed to upload files. Please try again.");
        return;
      }
    }

    const messageToSend = message.trim() || "[Files attached]";

    sendMessageMutation.mutate(
      { message: messageToSend, conversationId: undefined, documentIds },
      {
        onSuccess: (data: ChatResponse) => {
          router.push(`/dashboard/chat/${data.conversation_id}`);
        },
      }
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-900">Start a New Conversation</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="message"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            What would you like to discuss?
          </label>

          {/* Selected Files Display */}
          {selectedFiles.length > 0 && (
            <div className="mb-3 p-3 bg-gray-50 rounded-lg">
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

          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-gray-500 resize-none text-gray-900"
            rows={4}
            disabled={sendMessageMutation.isPending || isUploading}
            autoFocus
          />

          {/* File Upload Button */}
          <div className="mt-2">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileSelect}
              accept=".pdf,.txt,.docx"
              className="hidden"
              id="file-upload-new"
            />
            <label
              htmlFor="file-upload-new"
              className="inline-flex items-center px-3 py-1.5 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
            >
              <svg
                className="w-4 h-4 mr-2 text-gray-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                />
              </svg>
              Attach files
            </label>
            <span className="ml-2 text-xs text-gray-500">
              Supported: .pdf, .txt, .docx
            </span>
          </div>
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
          disabled={
            sendMessageMutation.isPending ||
            isUploading ||
            (!message.trim() && selectedFiles.length === 0)
          }
          className="w-full px-6 py-3 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
        >
          {sendMessageMutation.isPending || isUploading
            ? "Starting conversation..."
            : "Start Conversation"}
        </button>
      </form>

      <div className="mt-8 text-center">
        <Link
          href="/dashboard/chat/history"
          className="text-gray-700 hover:text-gray-900 text-sm font-medium"
        >
          View Conversation History →
        </Link>
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
