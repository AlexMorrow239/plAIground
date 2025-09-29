import { getApiUrl } from './env';

export class ApiClient {
  private static getHeaders(includeAuth: boolean = true): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (includeAuth) {
      const token = localStorage.getItem("access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  static async login(username: string, password: string) {
    const response = await fetch(getApiUrl('/api/auth/login'), {
      method: "POST",
      headers: ApiClient.getHeaders(false),
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    return response.json();
  }

  static async getDocuments() {
    const response = await fetch(getApiUrl('/api/documents/list'), {
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch documents");
    }

    return response.json();
  }

  static async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("access_token");
    const response = await fetch(getApiUrl('/api/documents/upload'), {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  static async deleteDocument(documentId: string) {
    const response = await fetch(getApiUrl(`/api/documents/${documentId}`), {
      method: "DELETE",
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to delete document");
    }

    return response.json();
  }

  static async sendChatMessage(message: string, conversationId?: string, documentIds?: string[]) {
    const response = await fetch(getApiUrl('/api/chat/send'), {
      method: "POST",
      headers: ApiClient.getHeaders(),
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        document_ids: documentIds,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  }

  static async getChatHistory() {
    const response = await fetch(getApiUrl('/api/chat/history'), {
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Clear invalid token and redirect to login
        localStorage.removeItem("access_token");
        localStorage.removeItem("session_id");
        localStorage.removeItem("expires_at");
        throw new Error("Authentication failed. Please login again.");
      }
      throw new Error(`Failed to fetch chat history: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log("API Response - Chat History:", data);
    return data;
  }

  static async clearConversation(conversationId: string) {
    const response = await fetch(getApiUrl(`/api/chat/history/${conversationId}`), {
      method: "DELETE",
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to clear conversation");
    }

    return response.json();
  }

  static async exportAllData() {
    const response = await fetch(getApiUrl('/api/export/all'), {
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to export data");
    }

    return response.json();
  }

  static async exportAsZip() {
    const response = await fetch(getApiUrl('/api/export/zip'), {
      headers: {
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`,
      },
    });

    if (!response.ok) {
      throw new Error("Failed to export data as ZIP");
    }

    // Return the blob directly for ZIP file
    return response.blob();
  }

  static async getSessionStatus() {
    const response = await fetch(getApiUrl('/api/auth/session'), {
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to get session status");
    }

    return response.json();
  }

  static async getDocumentContent(documentId: string) {
    const response = await fetch(getApiUrl(`/api/documents/${documentId}/content`), {
      headers: ApiClient.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch document content");
    }

    return response.json();
  }
}