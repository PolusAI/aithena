'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRabbitMQ } from '@/services/rabbitmq';
import StatusIndicator from './StatusIndicator';
import { useApiHealth } from '@/services/api';
import { useSettings } from '@/lib/settings';
import { createPortal } from 'react-dom';
import rabbitmqService from '@/services/rabbitmq';
import { useEndpoints } from '@/lib/hooks/useEndpoints';

interface DebugSectionProps {
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
    onToggle?: (isOpen: boolean) => void;
    parentRef?: React.RefObject<HTMLDivElement>;
}

const DebugSection: React.FC<DebugSectionProps> = ({ title, children, defaultOpen = false, onToggle, parentRef }) => {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    const contentRef = React.useRef<HTMLDivElement>(null);
    const [contentHeight, setContentHeight] = useState<number>(0);

    // Update content height when children change or when the section is opened/closed
    useEffect(() => {
        if (isOpen && contentRef.current) {
            const updateHeight = () => {
                if (contentRef.current) {
                    const newHeight = contentRef.current.scrollHeight;
                    setContentHeight(newHeight);

                    // If this is a nested section, notify parent to update its height
                    if (parentRef?.current) {
                        // Use setTimeout to ensure this happens after React rendering cycle
                        setTimeout(() => {
                            if (parentRef.current) {
                                const event = new Event('heightchange', { bubbles: true });
                                parentRef.current.dispatchEvent(event);
                            }
                        }, 0);
                    }
                }
            };

            updateHeight();

            // Create observer to watch for content height changes
            const resizeObserver = new ResizeObserver(updateHeight);
            resizeObserver.observe(contentRef.current);

            // Listen for height changes from nested sections
            const handleHeightChange = () => updateHeight();
            contentRef.current.addEventListener('heightchange', handleHeightChange);

            return () => {
                if (contentRef.current) {
                    resizeObserver.disconnect();
                    contentRef.current.removeEventListener('heightchange', handleHeightChange);
                }
            };
        }
    }, [isOpen, children, parentRef]);

    const handleToggle = () => {
        const newIsOpen = !isOpen;
        setIsOpen(newIsOpen);
        if (onToggle) onToggle(newIsOpen);
    };

    return (
        <div className="mb-4 rounded-xl overflow-hidden bg-white dark:bg-[#1e293b] border border-gray-200/50 dark:border-gray-700/50">
            <motion.button
                onClick={handleToggle}
                className="w-full px-4 py-3 text-left flex justify-between items-center hover:bg-gray-100 dark:hover:bg-[#252f44] transition-colors focus-ring cursor-pointer"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                transition={{ duration: 0.2 }}
            >
                <span className="font-medium text-gray-900 dark:text-white">{title}</span>
                <motion.div
                    initial={false}
                animate={{ rotate: isOpen ? 180 : 0 }}
                transition={{ duration: 0.1, ease: 'linear' }}
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="text-gray-500 dark:text-gray-400"
                    >
                        <path d="m6 9 6 6 6-6" />
                    </svg>
                </motion.div>
            </motion.button>
            <motion.div
                initial={false}
                animate={{
                    height: isOpen ? contentHeight : 0,
                    opacity: isOpen ? 1 : 0
                }}
                transition={{
                    duration: 0.15,
                    ease: 'linear'
                }}
                className="overflow-hidden"
            >
                <div
                    ref={contentRef}
                    className="px-4 py-3 border-t border-gray-200/50 dark:border-gray-700/50 text-sm bg-gray-50 dark:bg-[#1a2234]"
                >
                    {children}
                </div>
            </motion.div>
        </div>
    );
};

interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
    const { connected, statusUpdates } = useRabbitMQ();
    const { healthStatus, error: apiCheckError, loading: apiCheckLoading, refreshStatus } = useApiHealth();
    const { endpoints } = useEndpoints();
    
    // Development mode detection using runtime config from API
    const [isDevMode, setIsDevMode] = useState(false);
    
    useEffect(() => {
        // Fetch runtime configuration from API endpoint
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                const isDev = data.isDevelopment || false;
                setIsDevMode(isDev);
                console.log('[Sidebar] Environment check:', {
                    appEnv: data.appEnv,
                    nodeEnv: data.nodeEnv,
                    isDevelopment: data.isDevelopment,
                    isDevMode: isDev
                });
            })
            .catch(error => {
                console.error('[Sidebar] Failed to fetch config:', error);
                setIsDevMode(false);
            });
    }, []);
    
    const { settings, updateSettings } = useSettings();
    
    // Force refresh of connection status
    const [connectionStatus, setConnectionStatus] = useState(connected);
    const [mounted, setMounted] = useState(false);

    // Tooltip state
    const [showTooltip, setShowTooltip] = useState(false);
    const tooltipTimerRef = useRef<NodeJS.Timeout | null>(null);
    const tooltipButtonRef = useRef<HTMLButtonElement>(null);

    // Refs for nested DebugSections
    const debugPanelRef = React.useRef<HTMLDivElement>(null);
    const appearanceRef = React.useRef<HTMLDivElement>(null);
    const preferencesRef = React.useRef<HTMLDivElement>(null);

    // State for similarity_n input
    const [similarityN, setSimilarityN] = useState(settings.similarity_n);
    const [languages, setLanguages] = useState(settings.languages.join(', '));
    const [startYear, setStartYear] = useState(settings.start_year);
    const [endYear, setEndYear] = useState(settings.end_year);

    // Client-side rendering only
    useEffect(() => {
        setMounted(true);
        setSimilarityN(settings.similarity_n);
        setLanguages(settings.languages.join(', '));
        setStartYear(settings.start_year);
        setEndYear(settings.end_year);
    }, [settings.similarity_n, settings.languages, settings.start_year, settings.end_year]);

    // Handle tooltip display with delay to prevent flickering
    const handleTooltipMouseEnter = () => {
        if (tooltipTimerRef.current) {
            clearTimeout(tooltipTimerRef.current);
            tooltipTimerRef.current = null;
        }
        setShowTooltip(true);
    };

    const handleTooltipMouseLeave = () => {
        if (tooltipTimerRef.current) {
            clearTimeout(tooltipTimerRef.current);
        }
        tooltipTimerRef.current = setTimeout(() => {
            setShowTooltip(false);
        }, 300); // Increase delay to 300ms
    };

    // Clean up any pending timers on unmount
    useEffect(() => {
        return () => {
            if (tooltipTimerRef.current) {
                clearTimeout(tooltipTimerRef.current);
            }
        };
    }, []);

    // Handle similarity_n change
    const handleSimilarityNChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value, 10);
        if (!isNaN(value) && value > 0) {
            setSimilarityN(value);
        }
    };

    // Update global setting when user confirms
    const saveSimilarityN = () => {
        updateSettings({ similarity_n: similarityN });
    };

    const handleLanguageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setLanguages(e.target.value);
    };

    const handleStartYearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value, 10);
        setStartYear(isNaN(value) ? null : value);
    };

    const handleEndYearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value, 10);
        setEndYear(isNaN(value) ? null : value);
    };

    const saveFilters = () => {
        // Convert comma-separated string to array of languages
        const languagesArray = languages
            .split(',')
            .map(lang => lang.trim())
            .filter(lang => lang.length > 0);
        
        updateSettings({
            languages: languagesArray,
            start_year: startYear,
            end_year: endYear,
        });
    };

    // Check connection status when sidebar opens
    useEffect(() => {
        if (isOpen) {
            const isConnected = rabbitmqService.isConnected();
            setConnectionStatus(isConnected);

            // Set up connection change listener
            rabbitmqService.onConnectionChange((isConnected) => {
                setConnectionStatus(isConnected);
            });
        }
    }, [isOpen]);

    // Periodic connection status check
    useEffect(() => {
        if (!isOpen) return;

        const interval = setInterval(() => {
            const isConnected = rabbitmqService.isConnected();
            console.log('Periodic connection check:', isConnected);
            setConnectionStatus(isConnected);
        }, 5000); // Check every 5 seconds

        return () => clearInterval(interval);
    }, [isOpen]);

    // Update CSS variables when tooltip is shown
    useEffect(() => {
        if (showTooltip && tooltipButtonRef.current) {
            const rect = tooltipButtonRef.current.getBoundingClientRect();
            document.documentElement.style.setProperty('--tooltip-y', `${rect.top}px`);
            document.documentElement.style.setProperty('--tooltip-x', `${rect.left}px`);
        }
    }, [showTooltip]);

    const handleTestConnection = () => {
        const isConnected = rabbitmqService.isConnected();
        setConnectionStatus(isConnected);

        // Try to reconnect if not connected
        if (!isConnected) {
            rabbitmqService.connect().catch(error => {
                console.error('Failed to reconnect:', error);
            });
        }
    };

    if (!mounted) return null;

    return (
        <>
            {/* Settings Sidebar */}
            <motion.div
                className="fixed left-0 top-0 h-full w-80 bg-white dark:bg-[#1a2234] border-r border-gray-200/50 dark:border-gray-800/50 z-50 overflow-hidden"
                initial={{ x: '-100%' }}
                animate={{ x: isOpen ? 0 : '-100%' }}
                transition={{ type: 'spring', stiffness: 500, damping: 50 }}
            >
                <div className="h-full flex flex-col">
                    <div className="py-3 border-b border-gray-200/50 dark:border-gray-800/50">
                        <div className="h-14 px-4 flex items-center justify-between">
                            <motion.h2
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.1 }}
                                className="text-xl font-bold text-gray-900 dark:text-white"
                            >
                                Settings
                            </motion.h2>
                            <motion.button
                                onClick={onClose}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#252f44] transition-colors text-gray-600 dark:text-gray-400 focus-ring cursor-pointer"
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="18"
                                    height="18"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                >
                                    <path d="M18 6 6 18" />
                                    <path d="m6 6 12 12" />
                                </svg>
                            </motion.button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {/* Preferences Section - Always Visible */}
                        <DebugSection title="Preferences">
                            <div ref={preferencesRef} className="space-y-4">
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <div className="flex items-center gap-2">
                                            <label htmlFor="similarity_n" className="text-gray-700 dark:text-gray-300 font-medium">
                                                Document Limit
                                            </label>
                                            <div className="relative inline-block">
                                                <button
                                                    type="button"
                                                    className="flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors focus:outline-none"
                                                    onMouseEnter={handleTooltipMouseEnter}
                                                    onMouseLeave={handleTooltipMouseLeave}
                                                    onFocus={handleTooltipMouseEnter}
                                                    onBlur={handleTooltipMouseLeave}
                                                    onClick={() => setShowTooltip(!showTooltip)}
                                                    aria-label="More information about document limit"
                                                    ref={tooltipButtonRef}
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <circle cx="12" cy="12" r="10"></circle>
                                                        <path d="M12 16v-4"></path>
                                                        <path d="M12 8h.01"></path>
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <input
                                                id="similarity_n"
                                                type="number"
                                                min="1"
                                                max="100"
                                                value={similarityN}
                                                onChange={handleSimilarityNChange}
                                                onBlur={saveSimilarityN}
                                                className="w-16 px-2 py-1 text-right rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#252f44] text-gray-900 dark:text-white focus:border-primary-500 dark:focus:border-primary-400 focus:ring focus:ring-primary-500/20 dark:focus:ring-primary-400/20 outline-none"
                                            />
                                            <button
                                                onClick={saveSimilarityN}
                                                className="p-1 rounded-md bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 hover:bg-primary-200 dark:hover:bg-primary-800/40 transition-colors"
                                                title="Apply"
                                            >
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M20 6 9 17l-5-5" />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        Number of source documents used to answer your questions (default: 10)
                                    </p>
                                </div>
                                <DebugSection title="Filters" parentRef={preferencesRef}>
                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label htmlFor="language" className="text-gray-700 dark:text-gray-300 font-medium">
                                                Language
                                            </label>
                                            <input
                                                id="language"
                                                type="text"
                                                value={languages}
                                                onChange={handleLanguageChange}
                                                onBlur={saveFilters}
                                                className="w-full px-2 py-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#252f44] text-gray-900 dark:text-white focus:border-primary-500 dark:focus:border-primary-400 focus:ring focus:ring-primary-500/20 dark:focus:ring-primary-400/20 outline-none"
                                            />
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                Filter by language (e.g., 'en' or 'english'). Separate multiple languages with commas.
                                            </p>
                                        </div>
                                        <div className="space-y-2">
                                            <label htmlFor="start_year" className="text-gray-700 dark:text-gray-300 font-medium">
                                                Start Year
                                            </label>
                                            <input
                                                id="start_year"
                                                type="number"
                                                value={startYear ?? ''}
                                                onChange={handleStartYearChange}
                                                onBlur={saveFilters}
                                                className="w-full px-2 py-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#252f44] text-gray-900 dark:text-white focus:border-primary-500 dark:focus:border-primary-400 focus:ring focus:ring-primary-500/20 dark:focus:ring-primary-400/20 outline-none"
                                            />
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                Filter results published after this year
                                            </p>
                                        </div>
                                        <div className="space-y-2">
                                            <label htmlFor="end_year" className="text-gray-700 dark:text-gray-300 font-medium">
                                                End Year
                                            </label>
                                            <input
                                                id="end_year"
                                                type="number"
                                                value={endYear ?? ''}
                                                onChange={handleEndYearChange}
                                                onBlur={saveFilters}
                                                className="w-full px-2 py-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#252f44] text-gray-900 dark:text-white focus:border-primary-500 dark:focus:border-primary-400 focus:ring focus:ring-primary-500/20 dark:focus:ring-primary-400/20 outline-none"
                                            />
                                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                                Filter results published before this year
                                            </p>
                                        </div>
                                    </div>
                                </DebugSection>
                            </div>
                        </DebugSection>
                        
                        {/* Debug Panel Section (only visible in dev mode) */}
                        {isDevMode && (
                            <DebugSection title="Debug Panel" defaultOpen={true}>
                                <div ref={debugPanelRef} className="space-y-4">
                                    {/* RabbitMQ Status Section */}
                                    <DebugSection
                                        title="RabbitMQ Status"
                                        parentRef={debugPanelRef}
                                    >
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-gray-700 dark:text-gray-300">Connection:</span>
                                                <span className={`font-medium ${connectionStatus ? 'text-green-500' : 'text-red-500'}`}>
                                                    {connectionStatus ? 'Connected' : 'Disconnected'}
                                                </span>
                                            </div>
                                            <motion.button
                                                onClick={handleTestConnection}
                                                className="w-full bg-white hover:bg-gray-100 dark:bg-[#252f44] dark:hover:bg-[#2b374d] text-gray-900 dark:text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-ring"
                                                disabled={!connectionStatus}
                                                whileHover={connectionStatus ? { scale: 1.02 } : {}}
                                                whileTap={connectionStatus ? { scale: 0.98 } : {}}
                                            >
                                                Test Connection
                                            </motion.button>
                                        </div>
                                    </DebugSection>

                                    {/* API Status Section */}
                                    <DebugSection
                                        title="API Status"
                                        parentRef={debugPanelRef}
                                    >
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-gray-700 dark:text-gray-300">Status:</span>
                                                <span className={`font-medium ${healthStatus.status === 'ok' ? 'text-green-500' : 'text-red-500'}`}>
                                                    {healthStatus.status} {apiCheckLoading && '(checking...)'}
                                                </span>
                                            </div>

                                            {healthStatus.litellm && (
                                                <div className="flex items-center justify-between">
                                                    <span className="text-gray-700 dark:text-gray-300">LiteLLM:</span>
                                                    <span className={`font-medium ${healthStatus.litellm === 'connected' ? 'text-green-500' : 'text-red-500'}`}>
                                                        {healthStatus.litellm}
                                                    </span>
                                                </div>
                                            )}

                                            {healthStatus.api && (
                                                <div className="flex items-center justify-between">
                                                    <span className="text-gray-700 dark:text-gray-300">API Server:</span>
                                                    <span className={`font-medium ${healthStatus.api === 'running' ? 'text-green-500' : 'text-red-500'}`}>
                                                        {healthStatus.api}
                                                    </span>
                                                </div>
                                            )}

                                            {apiCheckError && (
                                                <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-xs">
                                                    Error: {apiCheckError}
                                                </div>
                                            )}

                                            <motion.button
                                                onClick={refreshStatus}
                                                className="w-full bg-white hover:bg-gray-100 dark:bg-[#252f44] dark:hover:bg-[#2b374d] text-gray-900 dark:text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-ring"
                                                disabled={apiCheckLoading}
                                                whileHover={!apiCheckLoading ? { scale: 1.02 } : {}}
                                                whileTap={!apiCheckLoading ? { scale: 0.98 } : {}}
                                            >
                                                {apiCheckLoading ? 'Checking...' : 'Refresh API Status'}
                                            </motion.button>
                                        </div>
                                    </DebugSection>

                                    {/* Environment Section */}
                                    <DebugSection
                                        title="Environment"
                                        parentRef={debugPanelRef}
                                    >
                                        <div className="space-y-3 text-sm">
                                            <div className="p-3 rounded-lg bg-white dark:bg-[#252f44]">
                                                <div className="text-gray-500 dark:text-gray-400 mb-1">Environment</div>
                                                <div className="text-gray-900 dark:text-white font-mono text-xs">
                                                    {process.env.NODE_ENV} - {endpoints?.apiUrl || 'Loading...'}
                                                </div>
                                            </div>
                                        </div>
                                    </DebugSection>

                                    {/* RabbitMQ Messages Section */}
                                    <DebugSection
                                        title="RabbitMQ Messages"
                                        parentRef={debugPanelRef}
                                    >
                                        <div className="max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-700 scrollbar-track-transparent rounded-lg">
                                            {statusUpdates.length > 0 ? (
                                                <StatusIndicator
                                                    statusUpdates={statusUpdates}
                                                    visible={true}
                                                    compact={true}
                                                    showAll={true}
                                                />
                                            ) : (
                                                <p className="text-gray-500 dark:text-gray-400 text-sm text-center py-4">No messages received yet</p>
                                            )}
                                        </div>
                                    </DebugSection>
                                </div>
                            </DebugSection>
                        )}

                    </div>
                </div>
            </motion.div>

            {/* Tooltip Component */}
            <Tooltip
                content={
                    <div>
                        Controls how many source documents Aithena retrieves to answer your question. More documents can provide better coverage but may slow down response time.
                    </div>
                }
                isVisible={showTooltip}
                anchorRef={tooltipButtonRef}
                onMouseEnter={handleTooltipMouseEnter}
                onMouseLeave={handleTooltipMouseLeave}
            />
        </>
    );
};

// Add a Tooltip component that uses createPortal
const Tooltip = ({
    content,
    isVisible,
    anchorRef,
    onMouseEnter,
    onMouseLeave
}: {
    content: React.ReactNode;
    isVisible: boolean;
    anchorRef: React.RefObject<HTMLElement>;
    onMouseEnter: () => void;
    onMouseLeave: () => void;
}) => {
    const [mounted, setMounted] = useState(false);
    const tooltipRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    useEffect(() => {
        if (!isVisible || !anchorRef.current || !tooltipRef.current) return;

        const updatePosition = () => {
            if (!anchorRef.current || !tooltipRef.current) return;

            const rect = anchorRef.current.getBoundingClientRect();
            const tooltipRect = tooltipRef.current.getBoundingClientRect();

            // Position tooltip above the button
            tooltipRef.current.style.left = `${rect.left - 10}px`;
            tooltipRef.current.style.top = `${rect.top - tooltipRect.height - 10}px`;
        };

        updatePosition();
        window.addEventListener('resize', updatePosition);
        window.addEventListener('scroll', updatePosition);

        return () => {
            window.removeEventListener('resize', updatePosition);
            window.removeEventListener('scroll', updatePosition);
        };
    }, [isVisible, anchorRef]);

    if (!mounted) return null;

    return createPortal(
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    ref={tooltipRef}
                    className="fixed px-3 py-2 w-64 bg-gray-800 dark:bg-gray-900 text-white text-xs rounded-md shadow-xl z-[9999]"
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{ maxWidth: '90vw' }}
                    onMouseEnter={onMouseEnter}
                    onMouseLeave={onMouseLeave}
                >
                    {content}
                    <div className="absolute w-3 h-3 bg-gray-800 dark:bg-gray-900 transform rotate-45 bottom-[-6px] left-[16px]"></div>
                </motion.div>
            )}
        </AnimatePresence>,
        document.body
    );
};

export default Sidebar;
