import { NextRequest, NextResponse } from 'next/server';
import { RABBITMQ_WS_URL } from '@/lib/server/config';
import 'server-only';
import { apiLogger } from '@/lib/logger';

export async function GET() {
    try {
        // Return proxy WebSocket URL that's relative to current origin
        // This ensures client always connects to the same server it's coming from
        // NEVER returning the internal Kubernetes service URL directly to client
        return NextResponse.json({
            wsUrl: '/askaithena/rabbitmq/ws',  // Updated to match nginx path
            exchange: 'ask-aithena-exchange'
        });
    } catch (error) {
        apiLogger.error('Failed to get RabbitMQ config', error);
        return NextResponse.json(
            { error: 'Failed to get RabbitMQ configuration' },
            { status: 500 }
        );
    }
}
