import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import React from 'react';
import Script from 'next/script';
import SettingsProvider from '@/lib/settings';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Ask Aithena',
    description: 'An intelligent research assistant powered by scientific knowledge',
    icons: {
        icon: '/favicon.ico',
    },
};

export const viewport: Viewport = {
    themeColor: [
        { media: '(prefers-color-scheme: light)', color: '#ffffff' },
        { media: '(prefers-color-scheme: dark)', color: '#0f172a' },
    ],
};

// This inline script is critical to prevent flash of incorrect theme
// It needs to execute synchronously before any rendering occurs
const themeInitScript = `
(function() {
  try {
    const theme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme;
  } catch (e) {}
})();
`;

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning className="scroll-smooth">
            <head>
                {/* Inline script to block rendering until theme is applied */}
                <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />

                <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=owl" />

                {/* Additional theme handling for more complex interactions */}
                <Script
                    id="theme-manager"
                    strategy="afterInteractive"
                >
                    {`
                    (function() {
                        try {
                            // Get theme preference from localStorage or system preference
                            function getThemePreference() {
                                if (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) {
                                    return localStorage.getItem('theme');
                                }
                                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                            }
                            
                            const theme = getThemePreference();
                            
                            // Save to localStorage if it came from system preference
                            if (!localStorage.getItem('theme')) {
                                localStorage.setItem('theme', theme);
                            }
                            
                            // Listen for theme changes from localStorage
                            window.addEventListener('storage', function() {
                                const updatedTheme = localStorage.getItem('theme');
                                if (updatedTheme === 'dark') {
                                    document.documentElement.classList.add('dark');
                                    document.documentElement.style.colorScheme = 'dark';
                                } else {
                                    document.documentElement.classList.remove('dark');
                                    document.documentElement.style.colorScheme = 'light';
                                }
                            });
                            
                            // Also listen for custom theme change event
                            window.addEventListener('themechange', function(e) {
                                const newTheme = e.detail?.theme;
                                if (newTheme === 'dark') {
                                    document.documentElement.classList.add('dark');
                                    document.documentElement.style.colorScheme = 'dark';
                                } else if (newTheme === 'light') {
                                    document.documentElement.classList.remove('dark');
                                    document.documentElement.style.colorScheme = 'light';
                                }
                            });
                        } catch (e) {
                            console.error('Error in theme manager:', e);
                        }
                    })();
                    `}
                </Script>
            </head>
            <body
                className={`${inter.className} bg-gradient-to-br from-gray-50 via-gray-50 to-gray-100 dark:from-[#0a0f1a] dark:via-[#0a0f1a] dark:to-[#0f172a] text-gray-900 dark:text-white min-h-screen overflow-hidden`}
            >
                <SettingsProvider>
                    <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary-500/5 via-transparent to-transparent dark:from-primary-500/10 pointer-events-none" />
                    <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-primary-600/[0.05] via-transparent to-transparent dark:from-primary-600/5 pointer-events-none" />
                    <div className="relative z-10">
                        {children}
                    </div>
                </SettingsProvider>
            </body>
        </html>
    );
} 