// Server-side only configuration
import 'server-only';
import getConfig from 'next/config';

// Get the server-side runtime configuration
const { serverRuntimeConfig, publicRuntimeConfig } = getConfig() || { 
    serverRuntimeConfig: {}, 
    publicRuntimeConfig: {} 
};

// During build time, environment variables may not be available
// So we provide placeholder values that will be replaced at runtime
// The actual validation happens in server.js at startup

// Internal URLs - used by server-side proxy to connect to backend services
function getInternalAPIUrl(): string {
    const url = serverRuntimeConfig.INTERNAL_API_URL || process.env.INTERNAL_API_URL;
    // During build, return placeholder. Runtime validation happens in server.js
    return url || '__INTERNAL_API_URL_NOT_SET__';
}

function getInternalRabbitMQWsUrl(): string {
    const url = serverRuntimeConfig.INTERNAL_RABBITMQ_WS_URL || process.env.INTERNAL_RABBITMQ_WS_URL;
    // During build, return placeholder. Runtime validation happens in server.js
    return url || '__INTERNAL_RABBITMQ_WS_URL_NOT_SET__';
}

// Public URLs - used by client-side code (should be relative paths for proxy mode)
function getPublicAPIUrl(): string {
    const url = publicRuntimeConfig.API_URL || process.env.NEXT_PUBLIC_API_URL;
    // During build, return placeholder. Runtime validation happens in server.js
    return url || '__API_URL_NOT_SET__';
}

function getPublicRabbitMQWsUrl(): string {
    const url = publicRuntimeConfig.RABBITMQ_WS_URL || process.env.NEXT_PUBLIC_RABBITMQ_WS_URL;
    // During build, return placeholder. Runtime validation happens in server.js
    return url || '__RABBITMQ_WS_URL_NOT_SET__';
}

// Internal URLs for server-side proxy
export const INTERNAL_API_URL = getInternalAPIUrl();
export const INTERNAL_RABBITMQ_WS_URL = getInternalRabbitMQWsUrl();

// Public URLs for client-side (kept for backward compatibility)
export const API_URL = getPublicAPIUrl();
export const RABBITMQ_WS_URL = getPublicRabbitMQWsUrl();
