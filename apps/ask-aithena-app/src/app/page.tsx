'use client';

import React, { useState, useEffect } from 'react';
import Chat from '@/components/Chat';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { AIMode } from '@/lib/types';
import { motion } from 'framer-motion';

export default function Home() {
    const [mode, setMode] = useState<AIMode>('owl');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const sidebarWidth = 320; // 80 * 4 = 320px (width in rem)

    const toggleSidebar = () => {
        setSidebarOpen(prev => !prev);

        // Dispatch a custom event to trigger citation reprocessing
        // Use a longer delay to ensure the sidebar transition is well underway
        setTimeout(() => {
            document.dispatchEvent(new CustomEvent('reprocessCitations'));
        }, 100); // Increased from 10ms to 100ms
    };

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <div className="relative flex-shrink-0" style={{ width: 0 }}>
                <Sidebar isOpen={sidebarOpen} onClose={toggleSidebar} />
            </div>

            {/* Main Content */}
            <motion.main
                className="flex flex-col flex-grow"
                animate={{
                    marginLeft: sidebarOpen ? `${sidebarWidth}px` : 0,
                }}
                transition={{
                    type: 'tween',
                    duration: 0.2,
                    ease: 'easeOut'
                }}
            >
                <Header
                    currentMode={mode}
                    onModeChange={setMode}
                    onToggleSidebar={toggleSidebar}
                />
                <div className="flex-1 overflow-hidden relative">
                    <div
                        className="absolute inset-0 overflow-y-auto [&::-webkit-scrollbar]:w-[16px] [&::-webkit-scrollbar-thumb]:bg-gray-500 dark:[&::-webkit-scrollbar-thumb]:bg-gray-600 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-[4px] [&::-webkit-scrollbar-thumb]:border-solid [&::-webkit-scrollbar-thumb]:border-transparent [&::-webkit-scrollbar-thumb]:bg-clip-padding [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:min-h-[40px]"
                    >
                        <Chat mode={mode} />
                    </div>
                </div>
            </motion.main>
        </div>
    );
} 