import { Message } from '@/types';
import { create } from 'zustand';

export interface PendingMessage extends Message {
  id: string;
  isPending: boolean;
  isThinking?: boolean;
}

// Empty array constant to avoid creating new references
const EMPTY_MESSAGES: PendingMessage[] = [];

interface ChatStore {
  // Map of chatId to pending messages
  pendingMessages: Map<string, PendingMessage[]>;

  // Add a pending user message
  addPendingUserMessage: (
    chatId: string,
    content: string,
    documentIds?: string[],
    documentContents?: Record<string, {
      filename: string;
      content: string;
      page_count?: number;
      word_count?: number;
    }>
  ) => string; // Returns message ID

  // Add a pending assistant "thinking" message
  addPendingAssistantMessage: (chatId: string) => string; // Returns message ID

  // Clear all pending messages for a chat
  clearPendingMessages: (chatId: string) => void;

  // Get pending messages for a specific chat
  getPendingMessages: (chatId: string) => PendingMessage[];

  // Clear all pending messages (for logout)
  clearAllPendingMessages: () => void;
}

// Utility to generate unique IDs
const generateId = () => `pending-${Date.now()}-${Math.random().toString(36).substring(7)}`;

// Selector hook for getting pending messages for a specific chat
export const usePendingMessages = (chatId: string) => {
  return useChatStore((state) => {
    const messages = state.pendingMessages.get(chatId);
    return messages || EMPTY_MESSAGES;
  });
};

export const useChatStore = create<ChatStore>((set, get) => ({
  pendingMessages: new Map(),

  addPendingUserMessage: (chatId, content, documentIds, documentContents) => {
    const messageId = generateId();
    const newMessage: PendingMessage = {
      id: messageId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      document_ids: documentIds,
      document_contents: documentContents,
      isPending: true,
    };

    set((state) => {
      const chatMessages = state.pendingMessages.get(chatId) || [];
      const updatedMap = new Map(state.pendingMessages);
      updatedMap.set(chatId, [...chatMessages, newMessage]);
      return { pendingMessages: updatedMap };
    });

    return messageId;
  },

  addPendingAssistantMessage: (chatId) => {
    const messageId = generateId();
    const thinkingMessage: PendingMessage = {
      id: messageId,
      role: 'assistant',
      content: '', // Content will be replaced by ThinkingIndicator
      timestamp: new Date().toISOString(),
      isPending: true,
      isThinking: true,
    };

    set((state) => {
      const chatMessages = state.pendingMessages.get(chatId) || [];
      const updatedMap = new Map(state.pendingMessages);
      updatedMap.set(chatId, [...chatMessages, thinkingMessage]);
      return { pendingMessages: updatedMap };
    });

    return messageId;
  },

  clearPendingMessages: (chatId) => {
    set((state) => {
      const updatedMap = new Map(state.pendingMessages);
      updatedMap.delete(chatId);
      return { pendingMessages: updatedMap };
    });
  },

  getPendingMessages: (chatId) => {
    return get().pendingMessages.get(chatId) || EMPTY_MESSAGES;
  },

  clearAllPendingMessages: () => {
    set({ pendingMessages: new Map() });
  },
}));
