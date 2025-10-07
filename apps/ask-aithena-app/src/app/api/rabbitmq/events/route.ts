import { NextRequest, NextResponse } from 'next/server';
import { RABBITMQ_WS_URL } from '@/lib/server/config';
import 'server-only';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
    try {
        const searchParams = request.nextUrl.searchParams;
        const sessionId = searchParams.get('sessionId');
        
        if (!sessionId) {
            return NextResponse.json(
                { error: 'Session ID is required' },
                { status: 400 }
            );
        }
        
        // For now, return a simple status message
        // In a real implementation, this would poll RabbitMQ for real status updates
        return NextResponse.json({
            status: 'ready',
            message: 'Status polling successful',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        console.error('Error in RabbitMQ events endpoint:', error);
        return NextResponse.json(
            { error: 'Failed to get RabbitMQ events' },
            { status: 500 }
        );
    }
} 