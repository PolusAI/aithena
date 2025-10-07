'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface ThemeToggleProps {
    className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = '' }) => {
    const [isDark, setIsDark] = useState(true);
    const [mounted, setMounted] = useState(false);

    // Initialize theme and apply transitions after mounting
    useEffect(() => {
        setMounted(true);

        // Get theme preference from localStorage or detect from DOM
        const savedTheme = localStorage.getItem('theme');
        const isDarkMode = savedTheme === 'dark' ||
            (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches) ||
            document.documentElement.classList.contains('dark');

        setIsDark(isDarkMode);

        // Add transition class immediately - use RAF to ensure it happens in next paint
        requestAnimationFrame(() => {
            document.documentElement.classList.add('theme-transitions-ready');
        });
    }, []);

    const toggleTheme = () => {
        const newIsDark = !isDark;
        setIsDark(newIsDark);
        const newTheme = newIsDark ? 'dark' : 'light';

        // Apply theme change directly in one batch of DOM operations
        requestAnimationFrame(() => {
            // Save to localStorage
            localStorage.setItem('theme', newTheme);

            // Update DOM 
            if (newIsDark) {
                document.documentElement.classList.add('dark');
                document.documentElement.style.colorScheme = 'dark';
            } else {
                document.documentElement.classList.remove('dark');
                document.documentElement.style.colorScheme = 'light';
            }

            // Force update the owl icon immediately
            const owlIcons = document.querySelectorAll('.material-symbols-outlined');
            owlIcons.forEach(icon => {
                if (icon.textContent?.trim() === 'owl') {
                    (icon as HTMLElement).style.color = 'inherit';
                    const parent = icon.parentElement as HTMLElement;
                    if (parent) {
                        parent.style.setProperty('color', 'var(--primary-color)', 'important');
                    }
                }
            });

            // Dispatch custom event for other components
            window.dispatchEvent(new CustomEvent('themechange', {
                detail: { theme: newTheme }
            }));

            // Also dispatch storage event for cross-tab syncing
            window.dispatchEvent(new StorageEvent('storage', {
                key: 'theme',
                newValue: newTheme,
                storageArea: localStorage
            }));
        });
    };

    // Don't render anything until mounted to prevent hydration mismatch
    if (!mounted) return null;

    return (
        <motion.button
            onClick={toggleTheme}
            className={`relative p-2.5 rounded-xl bg-gray-100 dark:bg-dark-200 hover:bg-gray-200 dark:hover:bg-dark-300 border border-gray-200/50 dark:border-gray-800/50 shadow-sm focus-ring cursor-pointer ${className}`}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
            initial={false}
            animate={{
                backgroundColor: isDark ? 'var(--dark-bg)' : 'var(--light-bg)',
            }}
            transition={{ duration: 0.2 }}
        >
            <motion.div
                initial={false}
                animate={{
                    rotate: isDark ? 180 : 0,
                }}
                transition={{ type: "spring", stiffness: 200, damping: 10 }}
            >
                {isDark ? (
                    <motion.svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="text-gray-700 dark:text-gray-300"
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.5, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <circle cx="12" cy="12" r="4" />
                        <path d="M12 2v2" />
                        <path d="M12 20v2" />
                        <path d="m4.93 4.93 1.41 1.41" />
                        <path d="m17.66 17.66 1.41 1.41" />
                        <path d="M2 12h2" />
                        <path d="M20 12h2" />
                        <path d="m6.34 17.66-1.41 1.41" />
                        <path d="m19.07 4.93-1.41 1.41" />
                    </motion.svg>
                ) : (
                    <motion.svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="text-gray-700"
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.5, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                    >
                        <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
                    </motion.svg>
                )}
            </motion.div>
        </motion.button>
    );
};

export default ThemeToggle; 