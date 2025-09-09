const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: this.getHeaders(false),
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Login failed");
    }

    return response.json();
  }

  static async getDocuments() {
    const response = await fetch(`${API_URL}/api/documents/list`, {
      headers: this.getHeaders(),
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
    const response = await fetch(`${API_URL}/api/documents/upload`, {
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
    const response = await fetch(`${API_URL}/api/documents/${documentId}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to delete document");
    }

    return response.json();
  }

  static async sendChatMessage(message: string, conversationId?: string) {
    const response = await fetch(`${API_URL}/api/chat/send`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to send message");
    }

    return response.json();
  }

  static async getChatHistory() {
    const response = await fetch(`${API_URL}/api/chat/history`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch chat history");
    }

    return response.json();
  }

  static async clearConversation(conversationId: string) {
    const response = await fetch(`${API_URL}/api/chat/history/${conversationId}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to clear conversation");
    }

    return response.json();
  }

  static async exportAllData() {
    const response = await fetch(`${API_URL}/api/export/all`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to export data");
    }

    return response.json();
  }

  static async getSessionStatus() {
    const response = await fetch(`${API_URL}/api/auth/session`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error("Failed to get session status");
    }

    return response.json();
  }
}