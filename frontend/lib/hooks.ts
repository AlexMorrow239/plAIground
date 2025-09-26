import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiClient } from "./api";

// Auth hooks
export function useLogin() {
  return useMutation({
    mutationFn: ({
      username,
      password,
    }: {
      username: string;
      password: string;
    }) => ApiClient.login(username, password),
    onSuccess: (data) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("session_id", data.session_id);

      // Calculate expires_at timestamp from expires_in (seconds)
      const expiresAt = new Date(Date.now() + data.expires_in * 1000);
      localStorage.setItem("expires_at", expiresAt.toISOString());
      localStorage.setItem("session_ttl_hours", data.session_ttl_hours);
    },
  });
}

// Document hooks
export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: ApiClient.getDocuments,
    enabled:
      typeof window !== "undefined" && !!localStorage.getItem("access_token"),
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => ApiClient.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (documentId: string) => ApiClient.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

// Chat hooks
export function useChatHistory() {
  return useQuery({
    queryKey: ["chat-history"],
    queryFn: ApiClient.getChatHistory,
    // Remove the enabled condition to let React Query handle retries
    // The ProtectedRoute will ensure we're authenticated before this runs
    retry: (
      failureCount,
      error: { message: string; status: number } | null
    ) => {
      // Don't retry on 401s
      if (error?.message?.includes("401") || error?.status === 401) {
        return false;
      }
      return failureCount < 2;
    },
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      message,
      conversationId,
      documentIds,
    }: {
      message: string;
      conversationId?: string;
      documentIds?: string[];
    }) => ApiClient.sendChatMessage(message, conversationId, documentIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-history"] });
    },
  });
}

export function useClearConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conversationId: string) =>
      ApiClient.clearConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-history"] });
    },
  });
}

// Export hooks
export function useExportData() {
  return useMutation({
    mutationFn: ApiClient.exportAllData,
    onSuccess: (data) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `legal-ai-research-export-${new Date().toISOString()}.json`;
      a.click();
    },
  });
}

// Session hooks
export function useSessionStatus() {
  return useQuery({
    queryKey: ["session-status"],
    queryFn: ApiClient.getSessionStatus,
    enabled:
      typeof window !== "undefined" && !!localStorage.getItem("access_token"),
    refetchInterval: 60000, // Refetch every minute
  });
}

// Document content hook
export function useDocumentContent(documentId: string) {
  return useQuery({
    queryKey: ["document-content", documentId],
    queryFn: () => ApiClient.getDocumentContent(documentId),
    enabled:
      typeof window !== "undefined" &&
      !!localStorage.getItem("access_token") &&
      !!documentId,
  });
}
