import { NextResponse } from "next/server";

/**
 * Returns the RabbitMQ WebSocket URL for the STOMP client.
 *
 * The URL is read from the RABBITMQ_WS_URL environment variable
 * (server-side only – not exposed to the browser bundle).
 * Defaults to "/api/rabbitmq/ws" which is resolved by the browser
 * against the current origin (works behind an Ingress/reverse proxy).
 */
export async function GET() {
  const wsUrl = process.env.RABBITMQ_WS_URL || "/api/rabbitmq/ws";

  return NextResponse.json({ wsUrl });
}
