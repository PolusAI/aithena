import { NextResponse } from 'next/server';

// Use NEXT_PUBLIC_APP_ENV which is available at runtime
// This is set as a Kubernetes environment variable
export async function GET() {
    // NEXT_PUBLIC_ vars are available at runtime in Next.js
    const appEnv = process.env.NEXT_PUBLIC_APP_ENV || process.env.APP_ENV || 'production';
    const nodeEnv = process.env.NODE_ENV || 'production';
    
    // Use APP_ENV as the primary control for debug mode
    const isDevelopment = appEnv === 'development';
    const isDevMode = appEnv === 'development';
    
    console.log('[API /config] Environment check:', {
        NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
        APP_ENV: process.env.APP_ENV,
        NODE_ENV: nodeEnv,
        isDevelopment,
        isDevMode
    });
    
    return NextResponse.json({
        appEnv,
        nodeEnv,
        isDevelopment,
        isDevMode,
        rabbitmqWsUrl: '/rabbitmq/ws',
        _debug: {
            version: '1.2.0-dev7',
            source: 'NEXT_PUBLIC_APP_ENV',
            NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
            APP_ENV: process.env.APP_ENV,
            NODE_ENV: process.env.NODE_ENV
        }
    });
}
