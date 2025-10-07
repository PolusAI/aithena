import { create } from 'zustand';
import { ChatState, Message } from '@/lib/types';
import { v4 as uuidv4 } from 'uuid';

export const useChatStore = create<ChatState>((set: any) => ({
    messages: [],
    loading: false,
    error: null,

    addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => set((state: ChatState) => ({
        messages: [
            ...state.messages,
            {
                ...message,
                id: uuidv4(),
                timestamp: new Date(),
            },
        ],
    })),

    updateLastAssistantMessage: (content: string) => set((state: ChatState) => {
        const messages = [...state.messages];
        const lastAssistantIndex = messages
            .map((msg, i) => msg.role === 'assistant' ? i : -1)
            .filter(i => i !== -1)
            .pop();

        if (lastAssistantIndex !== undefined) {
            messages[lastAssistantIndex] = {
                ...messages[lastAssistantIndex],
                content,
            };
        }

        return { messages };
    }),

    addReferencesToLastAssistantMessage: (references: string) => set((state: ChatState) => {
        const messages = [...state.messages];
        const lastAssistantIndex = messages
            .map((msg, i) => msg.role === 'assistant' ? i : -1)
            .filter(i => i !== -1)
            .pop();

        if (lastAssistantIndex !== undefined) {
            console.log('Adding references to last assistant message, length:', references.length);

            // Check if the message already has references and update or append them
            const currentReferences = messages[lastAssistantIndex].references || '';

            messages[lastAssistantIndex] = {
                ...messages[lastAssistantIndex],
                references: references, // Use the complete new references
            };
        } else {
            console.warn('No assistant message found to add references to');
        }

        return { messages };
    }),

    setLoading: (loading: boolean) => set({ loading }),

    setError: (error: string | null) => set({ error }),

    clearMessages: () => set({ messages: [] }),
})); 