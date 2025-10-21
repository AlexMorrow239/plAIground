export interface User {
  username: string;
  session_id: string;
}

export interface Document {
  document_id: string;
  filename: string;
  size_bytes: number;
  size_mb: number;
  upload_time: string;
  file_type: string;
  processed?: boolean;
  processing_error?: string | null;
  page_count?: number | null;
  word_count?: number | null;
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  document_ids?: string[];
  document_contents?: Record<string, {
    filename: string;
    content: string;
    page_count?: number;
    word_count?: number;
  }>;
}

// Extended message type for pending/optimistic updates
export interface PendingMessage extends Message {
  id: string;
  isPending: boolean;
  isThinking?: boolean; // For assistant "thinking" state
}

export interface Conversation {
  conversation_id: string;
  messages: Message[];
  created_at: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  document_ids?: string[];
}

export interface DocumentContent {
  document_id: string;
  filename: string;
  content: string;
  processed: boolean;
  processing_error?: string | null;
  page_count?: number | null;
  word_count?: number | null;
}

export interface SessionInfo {
  session_id: string;
  expires_at: string;
  time_remaining: number;
}

export interface ExportData {
  session_id: string;
  exported_at: string;
  documents: Document[];
  conversations: Conversation[];
}

export interface ApiError {
  detail: string;
}