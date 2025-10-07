import { NextRequest, NextResponse } from 'next/server';
import { request } from 'undici';
import { INTERNAL_API_URL } from '@/lib/server/config';
import { apiLogger } from '@/lib/logger';

export async function POST(req: NextRequest) {
    try {
        const { query, mode, sessionId, similarity_n, languages, start_year, end_year } = await req.json();
        
        // Make the request server-side using undici to internal service
        const { body, statusCode, headers } = await request(`${INTERNAL_API_URL}/${mode}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({ 
                query, 
                similarity_n,
                languages,
                start_year,
                end_year
            }),
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
        apiLogger.error('Error in ask route', error);
        return NextResponse.json(
            { error: 'Failed to process request' },
            { status: 500 }
        );
    }
}
