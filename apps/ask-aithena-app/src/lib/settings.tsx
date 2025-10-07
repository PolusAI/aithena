'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Settings } from '@/types/settings';

interface SettingsContextType {
    settings: Settings;
    updateSettings: (newSettings: Partial<Settings>) => void;
}

// Default settings
const defaultSettings: Settings = {
    similarity_n: 10,
    languages: ['en'],
    start_year: null,
    end_year: null,
};

// Create context with default values
const SettingsContext = createContext<SettingsContextType>({
    settings: defaultSettings,
    updateSettings: () => { },
});

// Custom hook to use settings
export const useSettings = () => useContext(SettingsContext);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    // Initialize state from localStorage if available, otherwise use defaults
    const [settings, setSettings] = useState<Settings>(() => {
        if (typeof window === 'undefined') return defaultSettings;

        const savedSettings = localStorage.getItem('app_settings');
        if (savedSettings) {
            try {
                return { ...defaultSettings, ...JSON.parse(savedSettings) };
            } catch (e) {
                console.error('Failed to parse settings from localStorage', e);
                return defaultSettings;
            }
        }
        return defaultSettings;
    });

    // Save settings to localStorage when they change
    useEffect(() => {
        if (typeof window !== 'undefined') {
            localStorage.setItem('app_settings', JSON.stringify(settings));
        }
    }, [settings]);

    // Function to update settings
    const updateSettings = (newSettings: Partial<Settings>) => {
        setSettings(prevSettings => ({
            ...prevSettings,
            ...newSettings,
        }));
    };

    return (
        <SettingsContext.Provider value={{ settings, updateSettings }}>
            {children}
        </SettingsContext.Provider>
    );
};

export default SettingsProvider;
