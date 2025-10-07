'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MessageItem from './MessageItem';
import ProcessingStatusCard from './ProcessingStatusCard';
import { useChatStore } from '@/store/chatStore';
import { askQuestion, /* continueConversation, */ parseStreamingResponse } from '@/services/api';
import { useRabbitMQ } from '@/services/rabbitmq';
import { AIMode } from '@/lib/types';
import { useSettings } from '@/lib/settings';
import { generateSessionId } from '@/lib/utils';
import SecureLogger from '@/lib/logger';

// Create a client-side logger instance
const chatLogger = new SecureLogger('Chat');

interface ChatProps {
    mode: AIMode;
}

const Chat: React.FC<ChatProps> = ({ mode }) => {
    const [query, setQuery] = useState('');
    const sessionIdRef = useRef(generateSessionId()); // Use ref instead of state
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const { messages, loading, error, addMessage, updateLastAssistantMessage, addReferencesToLastAssistantMessage, setLoading, setError } = useChatStore();
    const { clearStatusUpdates, statusUpdates, setSessionId } = useRabbitMQ();
    const { settings } = useSettings();

    // Track if we should hide status updates (after responding status is received)
    const [hideStatusAfterResponding, setHideStatusAfterResponding] = useState(false);
    const [mounted, setMounted] = useState(false);
    const [responseStartTime, setResponseStartTime] = useState<Date | null>(null);
    
    // Store shared references from the first assistant message
    const [sharedReferences, setSharedReferences] = useState<string | null>(null);
    
    // Global tooltip state - only one tooltip can exist at a time
    const [globalTooltip, setGlobalTooltip] = useState<{ ref: any; x: number; y: number } | null>(null);
    const hideTooltipTimeout = useRef<NodeJS.Timeout | null>(null);

    // Calculate the line height of the textarea dynamically
    const [lineHeight, setLineHeight] = useState(20); // Default estimate
    const maxLines = 10; // Show scrollbar after ~10 lines

    const hasUserScrolled = useRef(false);
    const chatContainerRef = useRef<HTMLDivElement>(null);

    // Reset hide status when starting a new query
    useEffect(() => {
        // Mark as mounted to prevent hydration issues
        setMounted(true);

        if (!loading) {
            setHideStatusAfterResponding(false);
            if (textareaRef.current) {
                textareaRef.current.focus();
            }
        }

        // Calculate accurate line height when component mounts
        if (mounted && textareaRef.current) {
            // Create a single line of text to measure height
            const originalValue = textareaRef.current.value;
            textareaRef.current.value = 'x';
            textareaRef.current.style.height = 'auto';
            const singleLineHeight = textareaRef.current.scrollHeight;

            // Add a new line to measure the difference
            textareaRef.current.value = 'x\nx';
            textareaRef.current.style.height = 'auto';
            const doubleLineHeight = textareaRef.current.scrollHeight;

            // Calculate actual line height
            const calculatedLineHeight = doubleLineHeight - singleLineHeight;
            setLineHeight(calculatedLineHeight > 0 ? calculatedLineHeight : 20);

            // Restore original value
            textareaRef.current.value = originalValue;
            resizeTextarea();
        }
    }, [loading, mounted]);

    // Cleanup tooltip timeout on unmount
    useEffect(() => {
        return () => {
            if (hideTooltipTimeout.current) {
                clearTimeout(hideTooltipTimeout.current);
            }
        };
    }, []);
    
    // Global tooltip handlers
    const showTooltip = (ref: any, x: number, y: number) => {
        // Clear any existing hide timeout
        if (hideTooltipTimeout.current) {
            clearTimeout(hideTooltipTimeout.current);
            hideTooltipTimeout.current = null;
        }
        setGlobalTooltip({ ref, x, y });
    };
    
    const hideTooltip = () => {
        // Add a small delay before hiding to prevent flickering
        hideTooltipTimeout.current = setTimeout(() => {
            setGlobalTooltip(null);
        }, 50); // Reduced delay for more responsive hiding
    };
    
    const hideTooltipImmediately = () => {
        if (hideTooltipTimeout.current) {
            clearTimeout(hideTooltipTimeout.current);
            hideTooltipTimeout.current = null;
        }
        setGlobalTooltip(null);
    };

    // Resize textarea based on content
    const resizeTextarea = () => {
        if (!textareaRef.current) return;

        const textarea = textareaRef.current;
        textarea.style.height = 'auto';

        const maxHeight = lineHeight * maxLines;
        const newHeight = Math.min(textarea.scrollHeight, maxHeight);
        textarea.style.height = newHeight + 'px';

        // Add or remove overflow class based on content height
        if (textarea.scrollHeight > maxHeight) {
            textarea.classList.add('overflow');
        } else {
            textarea.classList.remove('overflow');
        }
    };

    // Check for 'responding' status and capture response time
    useEffect(() => {
        if (statusUpdates.length > 0) {
            const latestStatus = statusUpdates[statusUpdates.length - 1].status;
            if (latestStatus === 'responding') {
                setResponseStartTime(new Date());
                setHideStatusAfterResponding(true);
            }
        }
    }, [statusUpdates]);

    // Check if user has scrolled up
    useEffect(() => {
        const container = chatContainerRef.current;
        if (!container) return;

        const handleScroll = () => {
            const { scrollTop, scrollHeight, clientHeight } = container;
            if (scrollHeight - scrollTop - clientHeight > 10) { // Small threshold
                hasUserScrolled.current = true;
            }
        };

        container.addEventListener('scroll', handleScroll, { passive: true });
        return () => container.removeEventListener('scroll', handleScroll);
    }, []);

    // Initialize session ID only once when component mounts
    useEffect(() => {
        chatLogger.debug('Initializing session ID');
        setSessionId(sessionIdRef.current);
    }, []); // Empty dependency array = run once on mount

    // Handle message updates and scrolling
    const updateMessageAndScroll = (content: string) => {
        // Update message first
        updateLastAssistantMessage(content);

        // Only scroll if user hasn't scrolled up and we're not animating
        if (!hasUserScrolled.current && chatContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 10;

            if (isAtBottom) {
                chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
            }
        }
    };

    const scrollToBottom = () => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const currentQuery = query.trim();
        if (!currentQuery || loading) return;

        try {
            setLoading(true);
            setQuery(''); // Clear input immediately after submission
            clearStatusUpdates();
            setHideStatusAfterResponding(false);
            hasUserScrolled.current = false; // Reset scroll state for new query

            // Add user message to chat
            addMessage({ role: 'user', content: currentQuery });
            addMessage({ role: 'assistant', content: '' });

            // Initial scroll to bottom for new query
            scrollToBottom();

            // Check if this is a follow-up conversation (has existing assistant messages)
            const hasConversationStarted = messages.some(msg => msg.role === 'assistant' && msg.content.trim() !== '');
            
            let response: Response;
            
            // if (hasConversationStarted) {
            //     // Build conversation history for talker agent
            //     const history = messages
            //         .filter(msg => msg.content.trim() !== '') // Filter out empty messages
            //         .map(msg => ({
            //             role: msg.role,
            //             content: msg.content
            //         }));
            //     
            //     // Add the current query to history
            //     history.push({ role: 'user', content: currentQuery });
            //     
            //     // Use talker endpoint for follow-up conversations
            //     response = await continueConversation(history, sessionIdRef.current);
            // } else {
                // First question - use the original endpoint with selected mode
                response = await askQuestion(
                    currentQuery, 
                    mode, 
                    sessionIdRef.current, 
                    settings.similarity_n,
                    settings.languages,
                    settings.start_year,
                    settings.end_year
                );
            // }

            // Use parseStreamingResponse to handle the stream
            const streamParser = parseStreamingResponse(response);
            let assistantMessage = '';
            let referencesPart = '';
            let captureReferences = false;

            for await (const chunk of streamParser) {
                if (hasUserScrolled.current) {
                    // If user has scrolled up, just update content without scrolling
                    if (captureReferences) {
                        referencesPart += chunk;
                    } else if (chunk.includes('\n\n\n')) {
                        captureReferences = true;
                        const [beforeSeparator, afterSeparator] = chunk.split('\n\n\n', 2);
                        assistantMessage += beforeSeparator;
                        if (afterSeparator) {
                            referencesPart = afterSeparator;
                        }
                        updateLastAssistantMessage(assistantMessage);
                    } else {
                        assistantMessage += chunk;
                        updateLastAssistantMessage(assistantMessage);
                    }
                } else {
                    // Normal flow with scrolling
                    if (captureReferences) {
                        referencesPart += chunk;
                    } else if (chunk.includes('\n\n\n')) {
                        captureReferences = true;
                        const [beforeSeparator, afterSeparator] = chunk.split('\n\n\n', 2);
                        assistantMessage += beforeSeparator;
                        if (afterSeparator) {
                            referencesPart = afterSeparator;
                        }
                        updateMessageAndScroll(assistantMessage);
                    } else {
                        assistantMessage += chunk;
                        updateMessageAndScroll(assistantMessage);
                    }
                }
            }

            // Apply references if found
            if (referencesPart.trim()) {
                addReferencesToLastAssistantMessage(referencesPart.trim());
                // Store references for sharing with subsequent messages
                setSharedReferences(referencesPart.trim());
                if (!hasUserScrolled.current) {
                    updateMessageAndScroll(assistantMessage);
                } else {
                    updateLastAssistantMessage(assistantMessage);
                }
            }

        } catch (err) {
            chatLogger.error('Error during message processing', err);
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    // Don't render anything until mounted to prevent hydration mismatch
    if (!mounted) return null;

    return (
        <div className="flex flex-col h-full relative">
            <div
                ref={chatContainerRef}
                className="chat-messages-container flex-1 overflow-y-auto [&::-webkit-scrollbar]:w-[60px] [&::-webkit-scrollbar-thumb]:bg-gray-500 dark:[&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-[24px] [&::-webkit-scrollbar-thumb]:border-solid [&::-webkit-scrollbar-thumb]:border-transparent [&::-webkit-scrollbar-thumb]:bg-clip-padding [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:min-h-[40px]"
            >
                {messages.length === 0 ? (
                    <div className="flex items-center justify-center h-full px-4">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="text-center max-w-xl w-full mx-auto bg-white dark:bg-[#1a2234] rounded-2xl shadow-lg shadow-black/5 dark:shadow-black/20 p-6 backdrop-blur-sm border border-gray-100 dark:border-gray-800/50"
                        >
                            <div className="mb-6">
                                <h2 className="text-3xl font-bold mb-3 text-gray-900 dark:text-white">Welcome to Ask Aithena</h2>
                                <p className="text-gray-600 dark:text-gray-300 text-lg leading-relaxed">
                                    Your intelligent research assistant. Ask any question and I'll provide detailed, evidence-based answers with references to scientific sources.
                                </p>
                            </div>
                            {/* <div className="space-y-3">
                                <motion.div
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.2 }}
                                    className="text-left p-4 rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 dark:from-[#141b2d] dark:to-[#1a2234] cursor-pointer hover:shadow-md transition-all duration-300"
                                    onClick={() => {
                                        setQuery("How does Aithena's context retrieval work?");
                                        setTimeout(() => {
                                            handleSubmit({ preventDefault: () => { } } as React.FormEvent);
                                        }, 100);
                                    }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-primary-500/10 dark:bg-primary-400/10">
                                            <svg className="w-5 h-5 text-primary-500 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        </div>
                                        <span className="text-gray-800 dark:text-gray-200">How does Aithena's context retrieval work?</span>
                                    </div>
                                </motion.div>
                                <motion.div
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.4 }}
                                    className="text-left p-4 rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 dark:from-[#141b2d] dark:to-[#1a2234] cursor-pointer hover:shadow-md transition-all duration-300"
                                    onClick={() => {
                                        setQuery("What's the difference between Owl, Shield, and Aegis modes?");
                                        setTimeout(() => {
                                            handleSubmit({ preventDefault: () => { } } as React.FormEvent);
                                        }, 100);
                                    }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-primary-500/10 dark:bg-primary-400/10">
                                            <svg className="w-5 h-5 text-primary-500 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                            </svg>
                                        </div>
                                        <span className="text-gray-800 dark:text-gray-200">What's the difference between Owl, Shield, and Aegis modes?</span>
                                    </div>
                                </motion.div>
                            </div> */}
                        </motion.div>
                    </div>
                ) : (
                    <div className="pt-4 pb-2 px-4">
                        <div className="max-w-4xl mx-auto">
                            {messages.map((message, index) => {
                                const isLastUserMessage =
                                    message.role === 'user' &&
                                    (index === messages.length - 1 ||
                                        (index === messages.length - 2 && messages[messages.length - 1].role === 'assistant'));

                                // Show all messages - user messages always, assistant messages if they have content or are being responded to
                                const isRespondingStatus = statusUpdates.length > 0 &&
                                    statusUpdates[statusUpdates.length - 1].status === 'responding';
                                const shouldShowMessage = message.role === 'user' ||
                                    (message.role === 'assistant' && (message.content || isRespondingStatus));

                                return shouldShowMessage ? (
                                    <React.Fragment key={message.id}>
                                        <MessageItem 
                                            message={message} 
                                            sharedReferences={message.role === 'assistant' && !message.references ? sharedReferences : null}
                                            onShowTooltip={showTooltip}
                                            onHideTooltip={hideTooltip}
                                            onHideTooltipImmediately={hideTooltipImmediately}
                                        />

                                        {/* Show ProcessingStatusCard after the last user message during loading and even after responding starts */}
                                        {isLastUserMessage && (
                                            <ProcessingStatusCard
                                                statusUpdates={statusUpdates}
                                                visible={statusUpdates.length > 0}
                                                responseStartTime={responseStartTime || undefined}
                                            />
                                        )}
                                    </React.Fragment>
                                ) : null;
                            })}
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {error && (
                <div className="flex justify-center">
                    <div className="w-full max-w-4xl px-4">
                        <div className="bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-600 text-red-800 dark:text-red-200 p-3 rounded-md mb-4">
                            {error}
                        </div>
                    </div>
                </div>
            )}

            <div className="pt-4 pb-2 px-4">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                    <div className="relative flex items-center gap-2">
                        <div className="flex-1 relative flex items-center">
                            <textarea
                                ref={textareaRef}
                                value={query}
                                onChange={(e) => {
                                    setQuery(e.target.value);
                                    resizeTextarea();
                                }}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        if (query.trim()) {
                                            handleSubmit(e as unknown as React.FormEvent);
                                        }
                                    }
                                }}
                                placeholder={`Ask a question in ${mode} mode...`}
                                className="w-full bg-white dark:bg-[#1a2234] border border-gray-200 dark:border-gray-800/50 text-gray-900 dark:text-white px-4 py-3.5 pr-12 rounded-xl focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500 outline-none resize-none min-h-[50px] overflow-hidden shadow-sm transition-[background,border,shadow] duration-200 ease-in-out hover:shadow-md [&.overflow]:overflow-y-auto [&.overflow]:scrollbar [&.overflow]:scrollbar-w-3 [&.overflow]:scrollbar-thumb-gray-300 dark:[&.overflow]:scrollbar-thumb-gray-600 [&.overflow]:scrollbar-track-transparent [&.overflow]:hover:scrollbar-thumb-gray-400 dark:[&.overflow]:hover:scrollbar-thumb-gray-500"
                                disabled={loading}
                                rows={1}
                            />
                            {!loading && query.trim() && (
                                <motion.div
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    exit={{ scale: 0.8, opacity: 0 }}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 z-10"
                                >
                                    <button
                                        type="submit"
                                        aria-label="Send message"
                                        className="p-3 rounded-full text-gray-900 dark:text-white transition-all duration-200 active:scale-95 cursor-pointer"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                            <path d="m22 2-7 20-4-9-9-4Z" />
                                            <path d="M22 2 11 13" />
                                        </svg>
                                    </button>
                                </motion.div>
                            )}
                            {loading && (
                                <motion.div
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    exit={{ scale: 0.8, opacity: 0 }}
                                    className="absolute right-2 top-1/2 -translate-y-1/2"
                                >
                                    <div className="p-2.5">
                                        <svg className="animate-spin h-[18px] w-[18px] text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                    </div>
                                </motion.div>
                            )}
                        </div>
                    </div>
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mt-2 text-xs text-gray-500 dark:text-gray-400"
                    >
                        Press Enter to send, Shift + Enter for new line
                    </motion.p>
                </form>
            </div>
            
            {/* Global Tooltip - only one can exist at a time */}
            {globalTooltip && (
                <div
                    className="citation-tooltip fixed z-50 bg-white/95 dark:bg-gray-950/98 shadow-lg rounded-md p-3.5 text-sm max-w-xs backdrop-blur-sm"
                    style={{
                        top: `${globalTooltip.y - 5}px`,
                        left: `${(() => {
                            const viewportWidth = window.innerWidth;
                            let left = globalTooltip.x;
                            // If tooltip would go off right edge, place it to the left
                            if (left + 300 > viewportWidth) {
                                left = globalTooltip.x - 310;
                            }
                            return left;
                        })()}px`,
                        pointerEvents: 'none'
                    }}
                >
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                        {globalTooltip.ref.title}
                    </div>
                    {globalTooltip.ref.year && (
                        <div className="text-gray-700 dark:text-gray-300 text-xs mt-1">
                            ({globalTooltip.ref.year})
                        </div>
                    )}
                    {globalTooltip.ref.authors && globalTooltip.ref.authors.length > 0 && (
                        <div className="text-gray-700 dark:text-gray-300 text-xs mt-1.5 line-clamp-1">
                            {globalTooltip.ref.authors.join(', ')}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// interface SuggestedQuestionProps {
//     text: string;
//     onClick: () => void;
// }

// const SuggestedQuestion: React.FC<SuggestedQuestionProps> = ({ text, onClick }) => (
//     <button
//         onClick={onClick}
//         className="text-left p-3 border border-gray-700 rounded-md bg-dark-100 hover:bg-dark-100/70 transition-colors text-gray-300"
//     >
//         {text}
//     </button>
// );

export default Chat;
