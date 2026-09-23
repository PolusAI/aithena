'use client';

import React, { FC, useState, useEffect, useRef } from 'react';
import { StatusUpdate } from '@/types/trialgpt';

interface TrialMatchStatusProps {
    statusUpdates: StatusUpdate[];
    visible: boolean;
    responseStartTime?: Date;
}

// GARDIAN pipeline status labels
const statusLabels: Record<string, string> = {
    'generating_keywords': 'Analyzing patient information and extracting key medical terms...',
    'generating_embedding': 'Creating semantic representation of patient case...',
    'retrieving_trials': 'Searching database for relevant clinical trials...',
    'matching_criteria': 'Analyzing eligibility criteria for candidate trials...',
    'matching_trial': 'Evaluating trial compatibility...',
    'ranking_trials': 'Calculating relevance and eligibility scores...',
    'responding': 'Processing complete, presenting results...',
};

const ThinkingDots: FC = () => (
    <div className="flex items-center justify-center gap-1">
        {[0, 0.2, 0.4].map((delay, i) => (
            <div
                key={i}
                className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400"
                style={{
                    animation: `bounce 1.2s infinite ease-in-out`,
                    animationDelay: `${delay}s`
                }}
            />
        ))}
        <style jsx>{`
            @keyframes bounce {
                0%, 80%, 100% {
                    transform: translateY(0);
                    opacity: 0.8;
                }
                40% {
                    transform: translateY(-8px);
                    opacity: 1;
                }
            }
        `}</style>
    </div>
);

const TrialMatchStatus: FC<TrialMatchStatusProps> = ({
    statusUpdates,
    visible,
    responseStartTime,
}) => {
    const [expanded, setExpanded] = useState(false);
    const [currentMessage, setCurrentMessage] = useState('');
    const [isResponding, setIsResponding] = useState(false);
    const [showCompletion, setShowCompletion] = useState(false);

    // Calculate processing time if we have a responseStartTime
    const calculateProcessingTime = () => {
        if (!responseStartTime || statusUpdates.length === 0) return null;

        const firstUpdateTime = statusUpdates[0].timestamp;
        const processingTimeMs = responseStartTime.getTime() - firstUpdateTime.getTime();
        const processingTimeSec = processingTimeMs / 1000;

        return processingTimeSec.toFixed(1);
    };

    const processingTime = calculateProcessingTime();

    // Process status updates to get messages
    useEffect(() => {
        if (!visible) {
            setCurrentMessage('');
            setIsResponding(false);
            setShowCompletion(false);
            return;
        }

        // Show an immediate message before RabbitMQ updates arrive
        if (statusUpdates.length === 0) {
            setCurrentMessage('Submitting request...');
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

        setCurrentMessage(newMessage);
    }, [statusUpdates, visible]);

    if (!visible) return null;

    return (
        <div className="mb-6 mt-2 relative">
            <div className="relative">
                <div
                    onClick={() => setExpanded(!expanded)}
                    className={`
                        cursor-pointer transition-all duration-200 
                        rounded-lg border border-gray-200 dark:border-gray-700
                        bg-white dark:bg-gray-800 hover:shadow-md
                        ${expanded ? 'mb-2' : ''}
                    `}
                >
                    <div className="flex items-center gap-3 py-3 px-4">
                        {/* Thinking/Completion indicator */}
                        <div className="flex items-center justify-center w-8 h-8">
                            {!showCompletion ? (
                                <ThinkingDots />
                            ) : (
                                <svg
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    className="w-6 h-6 text-green-600 dark:text-green-400"
                                    strokeWidth="3"
                                >
                                    <path
                                        d="M20 6L9 17L4 12"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    />
                                </svg>
                            )}
                        </div>

                        {/* Message container */}
                        <div className="flex-1">
                            <div className={`
                                text-sm
                                ${showCompletion
                                    ? 'text-green-700 dark:text-green-300 font-medium'
                                    : 'text-gray-700 dark:text-gray-200'
                                }
                            `}>
                                {isResponding && processingTime
                                    ? `Completed in ${processingTime} seconds`
                                    : currentMessage
                                }
                            </div>
                        </div>

                        {/* Expand indicator */}
                        <svg
                            className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                </div>

                {/* Expanded timeline view */}
                {expanded && (
                    <div className="pl-11 space-y-2 border-l-2 border-gray-200 dark:border-gray-700 ml-4">
                        {statusUpdates.map((update, index) => {
                            // Skip responding messages
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
                                <div key={index} className="flex items-center gap-3 py-1">
                                    <div className="w-2 h-2 rounded-full bg-blue-500/30 dark:bg-blue-400/30" />
                                    <div className="text-sm text-gray-600 dark:text-gray-300">
                                        {displayMessage}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TrialMatchStatus;
