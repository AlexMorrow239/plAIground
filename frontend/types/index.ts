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
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
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