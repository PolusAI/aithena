export type AIMode = 'owl' | 'shield' | 'aegis';

export interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    references?: string;
}

export interface ChatState {
    messages: Message[];
    loading: boolean;
    error: string | null;
    addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
    updateLastAssistantMessage: (content: string) => void;
    addReferencesToLastAssistantMessage: (references: string) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    clearMessages: () => void;
}

export interface StatusUpdate {
    status: string;
    timestamp: Date;
    message?: string;
} 