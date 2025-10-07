import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Runtime configuration approach - reads from a mounted config file
function getRuntimeConfig() {
    // First, check for a runtime config file (best practice for Kubernetes)
    const configPath = '/app/config/runtime.json';
    
    try {
        if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            console.log('[API /config] Runtime config loaded from file:', config);
            return config;
        }
    } catch (error) {
        console.error('[API /config] Error reading runtime config file:', error);
    }
    
    // Fallback to environment variables (for local development)
    // Note: In standalone builds, these are frozen at build time
    return {
        appEnv: process.env.APP_ENV || 'production',
        nodeEnv: process.env.NODE_ENV || 'production',
        rabbitmqWsUrl: process.env.NEXT_PUBLIC_RABBITMQ_WS_URL || '/rabbitmq/ws'
    };
}

export async function GET() {
    const config = getRuntimeConfig();
    
    const appEnv = config.appEnv || 'production';
    const nodeEnv = config.nodeEnv || 'production';
    
    // Use APP_ENV as the primary control for debug mode
    // NODE_ENV stays as 'production' in Docker
    const isDevelopment = appEnv === 'development';
    const isDevMode = appEnv === 'development';
    
    // Log for debugging
    console.log('[API /config] Environment check:', {
        APP_ENV: appEnv,
        NODE_ENV: nodeEnv,
        isDevelopment,
        isDevMode,
        source: fs.existsSync('/app/config/runtime.json') ? 'config-file' : 'environment'
    });
    
    return NextResponse.json({
        appEnv,
        nodeEnv,
        isDevelopment,
        isDevMode,
        rabbitmqWsUrl: config.rabbitmqWsUrl
    });
}

