'use client';

import React, { FC } from 'react';
import { motion } from 'framer-motion';
import { StatusUpdate } from '@/lib/types';
import { useEndpoints } from '@/lib/hooks/useEndpoints';

interface StatusIndicatorProps {
    statusUpdates: StatusUpdate[];
    visible: boolean;
    compact?: boolean;
    showAll?: boolean;
    showDebug?: boolean;
}

const statusLabels: Record<string, string> = {
    'retrieve_context': 'Retrieving relevant documents...',
    'analyzing_query': 'Analyzing your query...',
    'finding_relevant_documents': 'Finding relevant documents...',
    'rerank_context_one_step': 'Reviewing documents for relevance...',
    'aegis_rerank_context': 'Carefully reviewing every document retrieved, this may take a while...',
    'preparing_response': 'Preparing response...',
    'test_message': '🧪 Test message received!',
    'responding': 'Responding to your question...',
};

const StatusIndicator: FC<StatusIndicatorProps> = ({
    statusUpdates,
    visible,
    compact = false,
    showAll = false,
    showDebug = false
}) => {
    const { endpoints } = useEndpoints();
    const isDebug = process.env.NODE_ENV === 'development' && showDebug;

    if (!visible || statusUpdates.length === 0) return null;

    // Get the most recent status update for single display
    const latestUpdate = statusUpdates[statusUpdates.length - 1];
    const statusKey = latestUpdate.status.trim();
    const statusText = statusLabels[statusKey] || `Status: ${statusKey}`;

    // Development mode - show additional debug info
    const isDebugMode = process.env.NODE_ENV === 'development';

    // If showing all status updates (for debug panel)
    if (showAll) {
        return (
            <div className={`space-y-2 ${compact ? 'text-xs' : 'text-sm'}`}>
                {statusUpdates.slice().reverse().map((update, index) => {
                    const key = update.status.trim();
                    const text = statusLabels[key] || `Status: ${key}`;

                    return (
                        <div key={index} className="flex flex-col border-b border-gray-300 dark:border-gray-800 pb-2 last:border-0">
                            <div className="flex items-center">
                                {!compact && (
                                    <div className="relative mr-2 flex-shrink-0">
                                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--primary-color, #0da2e7)' }}></div>
                                    </div>
                                )}
                                <span className="text-gray-700 dark:text-gray-300">{text}</span>
                            </div>
                            {isDebug && (
                                <div className="text-xs text-gray-500 dark:text-gray-500 mt-1 pl-2">
                                    <span>Raw: {update.status}</span>
                                    <span className="ml-2">Time: {update.timestamp.toLocaleTimeString()}</span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        );
    }

    // Default single status display
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`flex flex-col p-3 bg-gray-100 dark:bg-gray-800/80 rounded-md mb-4 ${compact ? 'text-xs' : 'text-sm'}`}
        >
            <div className="flex items-center mb-1">
                {!compact && (
                    <div className="relative mr-3">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--primary-color, #0da2e7)' }}></div>
                        <motion.div
                            className="absolute -inset-1 rounded-full border-2"
                            style={{ borderColor: 'var(--primary-color, #0da2e7)' }}
                            animate={{ scale: [1, 1.5, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                        />
                    </div>
                )}
                <span className="text-gray-700 dark:text-gray-300">{statusText}</span>
            </div>

            {isDebug && (
                <div className="text-xs text-gray-500 dark:text-gray-500 mt-1 pl-6">
                    <span>Raw: {latestUpdate.status}</span>
                    <span className="ml-3">Time: {latestUpdate.timestamp.toLocaleTimeString()}</span>
                </div>
            )}
        </motion.div>
    );
};

export default StatusIndicator; 