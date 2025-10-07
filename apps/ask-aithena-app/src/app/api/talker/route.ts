import { NextRequest, NextResponse } from 'next/server';
import { request } from 'undici';
import { API_URL } from '@/lib/server/config';
import { apiLogger } from '@/lib/logger';

export async function POST(req: NextRequest) {
    try {
        const { history, sessionId } = await req.json();
        
        // Make the request to the talker endpoint using undici
        const { body, statusCode, headers } = await request(`${API_URL}/talker/talk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({ history }),
            // Timeout configuration
            bodyTimeout: 0, // No timeout for body streaming
            headersTimeout: 0, // No timeout for initial response
        });

        if (statusCode !== 200) {
            throw new Error(`API request failed with status: ${statusCode}`);
        }

        // Create a transform stream to handle the response
        const transformStream = new TransformStream();
        const writer = transformStream.writable.getWriter();
        
        // Process the stream
        (async () => {
            try {
                for await (const chunk of body) {
                    await writer.write(chunk);
                }
            } catch (error) {
                apiLogger.error('Error processing stream', error);
            } finally {
                await writer.close();
            }
        })();

        // Return the readable part of the transform stream
        return new NextResponse(transformStream.readable, {
            status: 200,
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        });
    } catch (error) {
        apiLogger.error('Error in talker route', error);
        return NextResponse.json(
            { error: 'Failed to process request' },
            { status: 500 }
        );
    }
}
