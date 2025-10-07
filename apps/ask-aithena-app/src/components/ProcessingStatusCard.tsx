'use client';

import React, { FC, useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { StatusUpdate } from '@/lib/types';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { CheckIcon } from '@heroicons/react/24/solid';

interface ProcessingStatusCardProps {
    statusUpdates: StatusUpdate[];
    visible: boolean;
    responseStartTime?: Date;
}

// Map of status keys to user-friendly messages
const statusLabels: Record<string, string> = {
    'retrieve_context': 'Retrieving relevant documents...',
    'analyzing_query': 'Analyzing your query...',
    'finding_relevant_documents': 'Finding relevant documents...',
    'rerank_context_one_step': 'Reviewing documents for relevance...',
    'aegis_rerank_context': 'Carefully reviewing every document retrieved...',
    'preparing_response': 'Preparing response...',
    'test_message': '🧪 Test message received!',
    'responding': 'Generating response...',
};

// Spring animation configs
const springTransition = {
    type: "spring",
    stiffness: 200,
    damping: 25,
    mass: 0.8
};

const ThinkingDots: FC = () => (
    <motion.div
        className="flex items-center justify-center gap-1"
        animate={{ rotate: [0, 0, 0, -3, 0] }}
        transition={{
            duration: 2.4,
            repeat: Infinity,
            ease: "easeInOut"
        }}
    >
        {[0, 0.2, 0.4].map((delay, i) => (
            <motion.div
                key={i}
                className="w-2 h-2 rounded-full bg-gray-700 dark:bg-gray-200"
                animate={{
                    y: [-4, 0, -4],
                    scale: [0.9, 1.1, 0.9],
                    opacity: [0.8, 1, 0.8],
                }}
                transition={{
                    duration: 1.2,
                    repeat: Infinity,
                    ease: [0.76, 0, 0.24, 1], // Custom easing for more organic motion
                    delay,
                }}
            />
        ))}
    </motion.div>
);

const ProcessingStatusCard: FC<ProcessingStatusCardProps> = ({
    statusUpdates,
    visible,
    responseStartTime,
}) => {
    const [expanded, setExpanded] = useState(false);
    const [currentMessage, setCurrentMessage] = useState('');
    const [previousMessage, setPreviousMessage] = useState('');
    const [transitioning, setTransitioning] = useState(false);
    const [isResponding, setIsResponding] = useState(false);
    const [showCompletion, setShowCompletion] = useState(false);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom of history list when expanded changes or new items are added
    useEffect(() => {
        if (!containerRef.current || !expanded) return;

        // No auto-scrolling, let parent component handle scrolling
    }, [expanded, statusUpdates]);

    // Calculate thinking time if we have a responseStartTime
    const calculateThinkingTime = () => {
        if (!responseStartTime || statusUpdates.length === 0) return null;

        const firstUpdateTime = statusUpdates[0].timestamp;
        const thinkingTimeMs = responseStartTime.getTime() - firstUpdateTime.getTime();
        const thinkingTimeSec = thinkingTimeMs / 1000;

        // Return thinking time with one decimal place
        return thinkingTimeSec.toFixed(1);
    };

    const thinkingTime = calculateThinkingTime();

    // Process status updates to get messages
    useEffect(() => {
        if (statusUpdates.length === 0 || !visible) {
            setCurrentMessage('');
            setPreviousMessage('');
            setIsResponding(false);
            setShowCompletion(false);
            return;
        }

        const latestUpdate = statusUpdates[statusUpdates.length - 1];
        const isRespondingStatus = latestUpdate.status === 'responding';
        setIsResponding(isRespondingStatus);

        // Set completion state when responding starts
        if (isRespondingStatus) {
            setTimeout(() => setShowCompletion(true), 400);
            return;
        }

        let newMessage = '';
        if (latestUpdate.message) {
            newMessage = latestUpdate.message;
        } else {
            try {
                const parsedStatus = JSON.parse(latestUpdate.status.trim());
                newMessage = parsedStatus.message || statusLabels[parsedStatus.status] || parsedStatus.status;
            } catch {
                newMessage = statusLabels[latestUpdate.status.trim()] || latestUpdate.status;
            }
        }

        if (newMessage !== currentMessage) {
            if (currentMessage) {
                setPreviousMessage(currentMessage);
                setTransitioning(true);
            }
            setCurrentMessage(newMessage);

            if (timeoutRef.current) clearTimeout(timeoutRef.current);
            timeoutRef.current = setTimeout(() => {
                setTransitioning(false);
            }, 600);
        }
    }, [statusUpdates, visible, currentMessage]);

    // Clean up timeout on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) clearTimeout(timeoutRef.current);
        };
    }, []);

    if (!visible || statusUpdates.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={springTransition}
            className={`mb-6 mt-0.5 px-6 relative ${showCompletion ? 'completion-state' : ''}`}
            ref={containerRef}
        >
            <div className="relative">
                <div
                    onClick={() => setExpanded(!expanded)}
                    className={`
                        cursor-pointer group transition-colors duration-200
                        ${expanded ? 'mb-1' : ''}
                        relative overflow-hidden rounded-xl
                    `}
                >
                    <div className="relative flex items-center gap-3 py-1.5 px-3">
                        {/* Thinking/Completion indicator */}
                        <div className="relative flex items-center justify-center w-8 h-8">
                            <AnimatePresence mode="wait">
                                {!showCompletion ? (
                                    <motion.div
                                        key="thinking"
                                        className="absolute inset-0 flex items-center justify-center"
                                        exit={{
                                            scale: 0.5,
                                            opacity: 0,
                                            filter: "blur(2px)",
                                            transition: {
                                                duration: 0.3,
                                                ease: [0.76, 0, 0.24, 1]
                                            }
                                        }}
                                    >
                                        <ThinkingDots />
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="completion"
                                        className="absolute inset-0 flex items-center justify-center"
                                        initial={{
                                            scale: 0.5,
                                            opacity: 0,
                                            filter: "blur(2px)"
                                        }}
                                        animate={{
                                            scale: 1,
                                            opacity: 1,
                                            filter: "blur(0px)"
                                        }}
                                        transition={{
                                            duration: 0.5,
                                            type: "spring",
                                            stiffness: 200,
                                            damping: 15
                                        }}
                                    >
                                        <motion.div
                                            initial={{ pathLength: 0, opacity: 0 }}
                                            animate={{ pathLength: 1, opacity: 1 }}
                                            transition={{
                                                duration: 0.8,
                                                ease: [0.76, 0, 0.24, 1]
                                            }}
                                            className="relative w-5 h-5"
                                        >
                                            <svg
                                                viewBox="0 0 24 24"
                                                fill="none"
                                                stroke="currentColor"
                                                className="w-5 h-5 text-gray-700 dark:text-gray-200"
                                                strokeWidth="3"
                                            >
                                                <motion.path
                                                    d="M20 6L9 17L4 12"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    initial={{ pathLength: 0 }}
                                                    animate={{ pathLength: 1 }}
                                                    transition={{
                                                        duration: 0.8,
                                                        ease: [0.76, 0, 0.24, 1]
                                                    }}
                                                />
                                            </svg>
                                        </motion.div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Message container */}
                        <div className="flex-1 overflow-hidden relative min-h-[28px]">
                            <AnimatePresence mode="popLayout">
                                {transitioning && previousMessage && (
                                    <motion.div
                                        key="previous"
                                        initial={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                        animate={{
                                            opacity: 0,
                                            y: -20,
                                            filter: "blur(2px)",
                                            scale: 0.98
                                        }}
                                        exit={{
                                            opacity: 0,
                                            y: -25,
                                            filter: "blur(3px)",
                                            scale: 0.97
                                        }}
                                        transition={{
                                            duration: 0.5,
                                            ease: [0.4, 0, 0.2, 1],
                                        }}
                                        className="absolute inset-0 flex items-center text-gray-600 dark:text-gray-300 text-sm"
                                        style={{
                                            backfaceVisibility: "hidden",
                                            WebkitFontSmoothing: "antialiased",
                                            transform: "translate3d(0,0,0)"
                                        }}
                                    >
                                        {previousMessage}
                                    </motion.div>
                                )}
                                <motion.div
                                    key="current"
                                    initial={{
                                        opacity: 0,
                                        y: 20,
                                        filter: "blur(2px)",
                                        scale: 1.01
                                    }}
                                    animate={{
                                        opacity: 1,
                                        y: 0,
                                        filter: "blur(0px)",
                                        scale: 1
                                    }}
                                    transition={{
                                        duration: 0.5,
                                        ease: [0.4, 0, 0.2, 1],
                                    }}
                                    className={`
                                        py-1 text-sm whitespace-pre-wrap break-words
                                        ${showCompletion
                                            ? 'text-primary-700 dark:text-primary-300 font-medium'
                                            : 'text-gray-700 dark:text-gray-200'
                                        }
                                    `}
                                    style={{
                                        backfaceVisibility: "hidden",
                                        WebkitFontSmoothing: "antialiased",
                                        transform: "translate3d(0,0,0)"
                                    }}
                                >
                                    {isResponding && thinkingTime
                                        ? `Reasoned and searched the database for ${thinkingTime} seconds`
                                        : currentMessage
                                    }
                                </motion.div>
                            </AnimatePresence>
                        </div>

                        {/* Expand indicator */}
                        <motion.div
                            animate={{ rotate: expanded ? 180 : 0 }}
                            transition={springTransition}
                            className="text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
                        >
                            <ChevronDownIcon className="h-4 w-4" />
                        </motion.div>
                    </div>
                </div>

                {/* Expanded timeline view */}
                <AnimatePresence mode="wait">
                    {expanded && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ ...springTransition, mass: 0.6 }}
                            className="relative pl-[44px] overflow-hidden"
                        >
                            {/* Timeline line with symmetric animation */}
                            <motion.div
                                className="absolute left-[7px] top-0 bottom-0 w-px"
                                initial={{ scaleY: 0, opacity: 0 }}
                                animate={{ scaleY: 1, opacity: 1 }}
                                exit={{ scaleY: 0, opacity: 0 }}
                                transition={{ ...springTransition, mass: 0.4 }}
                            >
                                <div className="h-full bg-gradient-to-b from-primary-500/20 via-primary-500/10 to-transparent dark:from-primary-400/20 dark:via-primary-400/10" />
                            </motion.div>

                            {/* Timeline items container with stagger effect */}
                            <motion.div
                                className="space-y-1.5 pt-0.5"
                                initial="collapsed"
                                animate="expanded"
                                exit="collapsed"
                                variants={{
                                    expanded: {
                                        transition: {
                                            staggerChildren: 0.1
                                        }
                                    },
                                    collapsed: {
                                        transition: {
                                            staggerChildren: 0.05,
                                            staggerDirection: -1
                                        }
                                    }
                                }}
                            >
                                {statusUpdates.map((update, index) => {
                                    // Skip ALL responding messages - they are only used as completion signals
                                    if (update.status === 'responding') return null;

                                    let displayMessage = update.message;
                                    if (!displayMessage) {
                                        try {
                                            const parsedStatus = JSON.parse(update.status.trim());
                                            displayMessage = parsedStatus.message || statusLabels[parsedStatus.status] || parsedStatus.status;
                                        } catch {
                                            displayMessage = statusLabels[update.status.trim()] || update.status;
                                        }
                                    }
                                    if (!displayMessage) return null;

                                    return (
                                        <motion.div
                                            key={index}
                                            variants={{
                                                expanded: {
                                                    opacity: 1,
                                                    x: 0,
                                                    transition: {
                                                        ...springTransition,
                                                        mass: 0.2
                                                    }
                                                },
                                                collapsed: {
                                                    opacity: 0,
                                                    x: -10,
                                                    transition: {
                                                        ...springTransition,
                                                        mass: 0.1
                                                    }
                                                }
                                            }}
                                            className="flex items-center gap-3 group -ml-[5px]"
                                        >
                                            <motion.div
                                                variants={{
                                                    expanded: {
                                                        scale: 1,
                                                        opacity: 1
                                                    },
                                                    collapsed: {
                                                        scale: 0.5,
                                                        opacity: 0
                                                    }
                                                }}
                                                className="w-2 h-2 rounded-full bg-primary-500/30 dark:bg-primary-400/30
                                                         group-hover:bg-primary-500/50 dark:group-hover:bg-primary-400/50
                                                         transition-colors duration-200"
                                            />
                                            <div className="text-sm text-gray-600 dark:text-gray-300
                                                          group-hover:text-gray-800 dark:group-hover:text-gray-100
                                                          transition-colors duration-200">
                                                {displayMessage}
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Add styles for completion particles */}
            <style jsx global>{`
                @keyframes fadeInOut {
                    0%, 100% { opacity: 0; }
                    50% { opacity: 1; }
                }

                .completion-state {
                    position: relative;
                }

                .completion-state::before {
                    content: '';
                    position: absolute;
                    inset: 0;
                    background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), 
                                              rgba(var(--primary-rgb), 0.08) 0%,
                                              transparent 70%);
                    opacity: 0;
                    animation: fadeInOut 2s ease-in-out infinite;
                    pointer-events: none;
                    filter: blur(8px);
                }

                .completion-state::after {
                    content: '';
                    position: absolute;
                    inset: 0;
                    background: radial-gradient(circle at var(--x, 50%) var(--y, 50%), 
                                              rgba(var(--primary-rgb), 0.05) 0%,
                                              transparent 60%);
                    opacity: 0;
                    animation: fadeInOut 3s ease-in-out infinite;
                    animation-delay: 1s;
                    pointer-events: none;
                    filter: blur(4px);
                }

                @property --x {
                    syntax: '<percentage>';
                    initial-value: 50%;
                    inherits: false;
                }

                @property --y {
                    syntax: '<percentage>';
                    initial-value: 50%;
                    inherits: false;
                }
            `}</style>
        </motion.div>
    );
};

export default ProcessingStatusCard; 