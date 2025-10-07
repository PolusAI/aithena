'use client';

import React, { FC, useState } from 'react';
import { AIMode } from '@/lib/types';
import { motion, AnimatePresence } from 'framer-motion';
import ThemeToggle from './ThemeToggle';

interface HeaderProps {
    currentMode: AIMode;
    onModeChange: (mode: AIMode) => void;
    onToggleSidebar: () => void;
}

interface ModeInfoModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const ModeInfoModal: FC<ModeInfoModalProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={onClose}
        >
            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                className="bg-white dark:bg-[#1a2234] rounded-xl p-6 max-w-2xl mx-4 shadow-xl border border-gray-200/50 dark:border-gray-800/50"
                onClick={(e: React.MouseEvent) => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ask Aithena Modes</h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#252f44] transition-colors text-gray-600 dark:text-gray-400 cursor-pointer"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M18 6 6 18" />
                            <path d="m6 6 12 12" />
                        </svg>
                    </button>
                </div>
                <div className="space-y-6">
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Owl Mode
                        </h3>
                        <p className="text-gray-600 dark:text-gray-300">Think of me as a wise owl - quick and direct. In this mode, I'll swiftly find the most relevant documents to answer your question. I'll use my semantic search abilities to fetch what you need, but I won't spend extra time double-checking or analyzing the results. This is perfect when you need fast, straightforward answers!</p>
                    </div>
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Shield Mode
                        </h3>
                        <p className="text-gray-600 dark:text-gray-300">Like a shield that offers reliable protection, in this mode I take an extra step to verify the quality and relevance of each document I find. After my initial search, I carefully review how well each piece of information matches your specific question, ensuring better accuracy. It's like having a second pair of eyes review everything before answering. Great for when you need more precise, well-vetted information!</p>
                    </div>
                    <div className="space-y-3">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Aegis Mode
                        </h3>
                        <p className="text-gray-600 dark:text-gray-300">Named after Zeus's legendary shield, this is my most thorough mode. I not only find relevant documents but also perform an extensive multi-step analysis to evaluate how each piece of information connects to your question. I'll carefully examine context, look for deeper connections, and ensure maximum accuracy. Perfect for complex questions or when you need the highest level of confidence in the answer!</p>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
};

const Header: FC<HeaderProps> = ({ currentMode, onModeChange, onToggleSidebar }) => {
    const [showModeInfo, setShowModeInfo] = useState(false);

    return (
        <motion.header
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="bg-white dark:bg-[#1a2234] sticky top-0 z-50 border-b border-gray-200/50 dark:border-gray-800/50 py-3"
        >
            <div className="container mx-auto px-4 flex items-center justify-between h-14">
                <div className="flex items-center gap-3">
                    <motion.button
                        onClick={onToggleSidebar}
                        className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white p-2 rounded-lg transition-colors hover:bg-gray-100 dark:hover:bg-[#252f44] focus-ring cursor-pointer"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <line x1="3" y1="12" x2="21" y2="12" />
                            <line x1="3" y1="6" x2="21" y2="6" />
                            <line x1="3" y1="18" x2="21" y2="18" />
                        </svg>
                    </motion.button>
                    <motion.div
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="flex items-center gap-3"
                    >
                        <span className="material-symbols-outlined text-primary-500 dark:text-primary-400" style={{
                            fontSize: '24px',
                            transition: 'none !important',
                        }}>
                            owl
                        </span>
                        <motion.h1
                            className="text-xl font-bold text-gray-900 dark:text-white"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            Ask Aithena
                        </motion.h1>
                    </motion.div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <motion.button
                            onClick={() => setShowModeInfo(true)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-[#252f44] transition-colors text-gray-600 dark:text-gray-400 focus-ring cursor-pointer"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <path d="M12 16v-4"></path>
                                <path d="M12 8h.01"></path>
                            </svg>
                        </motion.button>
                        <div className="p-1 bg-gray-100 dark:bg-[#0f172a] rounded-lg border border-gray-200/50 dark:border-gray-800/50 shadow-sm flex items-center">
                            <ModeButton
                                mode="owl"
                                currentMode={currentMode}
                                onModeChange={onModeChange}
                                label="Owl"
                            />
                            <ModeButton
                                mode="shield"
                                currentMode={currentMode}
                                onModeChange={onModeChange}
                                label="Shield"
                            />
                            <ModeButton
                                mode="aegis"
                                currentMode={currentMode}
                                onModeChange={onModeChange}
                                label="Aegis"
                            />
                        </div>
                    </div>
                    <ThemeToggle />
                </div>
            </div>
            <AnimatePresence>
                <ModeInfoModal isOpen={showModeInfo} onClose={() => setShowModeInfo(false)} />
            </AnimatePresence>
        </motion.header>
    );
};

interface ModeButtonProps {
    mode: AIMode;
    currentMode: AIMode;
    onModeChange: (mode: AIMode) => void;
    label: string;
}

const getTooltipText = (mode: AIMode) => {
    switch (mode) {
        case 'owl':
            return 'Quick and direct';
        case 'shield':
            return 'Better accuracy';
        case 'aegis':
            return 'Maximum confidence';
        default:
            return '';
    }
};

const ModeButton: FC<ModeButtonProps> = ({
    mode,
    currentMode,
    onModeChange,
    label,
}) => {
    const isActive = mode === currentMode;
    const [showTooltip, setShowTooltip] = useState(false);

    return (
        <div className="relative">
            <motion.button
                onClick={() => onModeChange(mode)}
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                className={`relative px-3 py-1.5 rounded-md text-sm transition-all duration-200 focus-ring cursor-pointer ${isActive
                    ? 'text-white font-medium'
                    : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                whileHover={!isActive ? { scale: 1.05 } : {}}
                whileTap={!isActive ? { scale: 0.95 } : {}}
            >
                <span className="relative z-10">{label}</span>
                {isActive && (
                    <motion.div
                        layoutId="activeMode"
                        className="absolute inset-0 rounded-md shadow-md dark:shadow-lg dark:shadow-primary-500/20"
                        style={{
                            background: 'linear-gradient(135deg, var(--primary-color) 0%, #0284c7 100%)',
                        }}
                        initial={false}
                        transition={{
                            type: 'spring',
                            stiffness: 200,
                            damping: 20
                        }}
                    />
                )}
            </motion.button>
            <AnimatePresence>
                {showTooltip && (
                    <motion.div
                        initial={{ opacity: 0, y: -2 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -2 }}
                        className="absolute left-1/2 -translate-x-1/2 top-full mt-1 px-2 py-1 text-xs rounded bg-gray-900 dark:bg-gray-700 text-white whitespace-nowrap z-50"
                    >
                        {getTooltipText(mode)}
                        <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-gray-900 dark:bg-gray-700 rotate-45" />
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Header; 