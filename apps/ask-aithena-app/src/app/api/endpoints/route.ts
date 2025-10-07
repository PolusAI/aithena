import { NextResponse } from 'next/server';

export async function GET() {
    // Hardcoded public URLs - these are part of the application's API contract
    // They don't change between environments, only the backend services they proxy to change
    const endpoints = {
        apiUrl: '/api',
        rabbitmqWsUrl: '/rabbitmq/ws'
    };
    
    console.log('[API /endpoints] Serving endpoints:', endpoints);
    
    return NextResponse.json(endpoints);
}
