'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRabbitMQ } from '@/services/rabbitmq';
import TrialMatchStatus from './TrialMatchStatus';
import TrialResultCard from './TrialResultCard';
import { TrialMatchResponse } from '@/types/trialgpt';
import { api } from '@/services/api';

// Generate a simple session ID
function generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

const TrialGPTChat: React.FC = () => {
    const [clinicalNote, setClinicalNote] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<TrialMatchResponse | null>(null);
    const [responseStartTime, setResponseStartTime] = useState<Date | null>(null);
    const [sessionId, setSessionId] = useState('');
    const [conceptsOpen, setConceptsOpen] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const { statusUpdates, clearStatusUpdates, setSessionId: setRabbitMQSessionId } = useRabbitMQ();

    // Generate session ID on mount
    useEffect(() => {
        const newSessionId = generateSessionId();
        setSessionId(newSessionId);
        setRabbitMQSessionId(newSessionId);
    }, [setRabbitMQSessionId]);

    // Check for 'responding' status
    useEffect(() => {
        if (statusUpdates.length > 0) {
            const latestStatus = statusUpdates[statusUpdates.length - 1].status;
            if (latestStatus === 'responding') {
                setResponseStartTime(new Date());
            }
        }
    }, [statusUpdates]);

    // Auto-resize textarea to fit content
    const autoResize = useCallback(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = 'auto';
        // Min 3 rows (~72px), max ~50vh
        const minH = 72;
        const maxH = window.innerHeight * 0.5;
        el.style.height = `${Math.min(Math.max(el.scrollHeight, minH), maxH)}px`;
    }, []);

    const handleNoteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setClinicalNote(e.target.value);
        autoResize();
    };

    // Resize on mount / clear
    useEffect(() => { autoResize(); }, [clinicalNote, autoResize]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!clinicalNote.trim()) {
            setError('Please enter patient clinical information');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setResults(null);
            setConceptsOpen(false);
            clearStatusUpdates();
            setResponseStartTime(null);

            const data = await api.matchPatient({
                clinical_note: clinicalNote,
                top_n: 20,
                retrieval_method: 'hybrid',
                session_id: sessionId,
            });

            setResults(data);
        } catch (err) {
            console.error('Error matching trials:', err);
            setError(err instanceof Error ? err.message : 'Failed to match trials');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-6">
                <h2 className="text-2xl font-semibold tracking-tight mb-1">
                    <span className="text-[#7f2754]">GARD</span><span className="text-[#1b568b] dark:text-[#00d4ff]">IAN</span> Patient Matching
                </h2>
                <p className="text-sm text-[var(--color-muted-foreground)]">
                    Enter a clinical note for a rare disease patient to find matching clinical trials.
                </p>
            </div>

            {/* Input Form */}
            <form onSubmit={handleSubmit} className="mb-6 space-y-4">
                <div>
                    <label htmlFor="clinical-note" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Patient Clinical Note
                    </label>
                    <textarea
                        ref={textareaRef}
                        id="clinical-note"
                        value={clinicalNote}
                        onChange={handleNoteChange}
                        placeholder="Enter patient clinical history, symptoms, diagnoses, medications, and relevant medical information..."
                        className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-gray-100 resize-none overflow-hidden"
                        style={{ minHeight: '72px' }}
                        disabled={loading}
                    />
                </div>

                {error && (
                    <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                        <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                    </div>
                )}

                <button
                    type="submit"
                    disabled={loading || !clinicalNote.trim()}
                    className="w-full bg-[#1b568b] hover:bg-[#154575] disabled:bg-gray-400 text-white font-semibold py-2.5 px-6 rounded-lg transition-colors disabled:cursor-not-allowed"
                >
                    {loading ? 'Finding Matching Trials...' : 'Find Matching Trials'}
                </button>
            </form>

            {/* Status Updates */}
            {loading && (
                <TrialMatchStatus
                    statusUpdates={statusUpdates}
                    visible={loading}
                    responseStartTime={responseStartTime ?? undefined}
                />
            )}

            {/* Results */}
            {results && (
                <div className="space-y-4">
                    {/* Extracted Medical Concepts (collapsible) */}
                    {results.keywords_generated && (
                        <div className="border border-blue-200 dark:border-blue-800 rounded-lg overflow-hidden">
                            <button
                                type="button"
                                onClick={() => setConceptsOpen(!conceptsOpen)}
                                className="w-full flex items-center justify-between px-4 py-2.5 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors text-left"
                            >
                                <span className="font-semibold text-sm text-blue-900 dark:text-blue-100">
                                    Extracted Medical Concepts ({results.keywords_generated.conditions.length})
                                </span>
                                <svg
                                    className={`w-4 h-4 text-blue-600 dark:text-blue-400 transition-transform ${conceptsOpen ? 'rotate-180' : ''}`}
                                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            {conceptsOpen && (
                                <div className="px-4 py-3 bg-blue-50/50 dark:bg-blue-900/10">
                                    <p className="text-sm text-blue-800 dark:text-blue-200 mb-2">
                                        {results.keywords_generated.summary}
                                    </p>
                                    <div className="flex flex-wrap gap-1.5">
                                        {results.keywords_generated.conditions.map((condition, idx) => (
                                            <span
                                                key={idx}
                                                className="inline-block px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded"
                                            >
                                                {condition}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Summary */}
                    <div className="flex items-center justify-between px-1">
                        <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                            {results.results.length} Matching Trials
                        </h2>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                            {(results.execution_time_ms / 1000).toFixed(1)}s
                        </span>
                    </div>

                    {/* Trial Results */}
                    <div className="space-y-3">
                        {results.results.map((trial) => (
                            <TrialResultCard key={trial.nct_id} trial={trial} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TrialGPTChat;
