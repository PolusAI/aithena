// Load environment variables from .env.local (for local development only)
// In production, environment variables come from Kubernetes ConfigMap
try {
    require('dotenv').config({ path: '.env.local' });
} catch (e) {
    // dotenv is not available in production, which is fine
}

const http = require('http');
const { parse } = require('url');
const next = require('next');
const httpProxy = require('http-proxy');
const fs = require('fs');

// Load runtime configuration
function loadRuntimeConfig() {
    // Try to load from mounted config file in Kubernetes
    const configPath = '/app/config/runtime.json';
    
    try {
        if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            console.log('✓ Runtime config loaded from:', configPath);
            return config;
        }
    } catch (error) {
        console.error('Error reading runtime config file:', error);
    }
    
    // Fallback to environment variables for local development
    console.log('⚠ Using environment variables (config file not found)');
    return {
        appEnv: process.env.APP_ENV || 'production',
        internalApiUrl: process.env.INTERNAL_API_URL || 'http://localhost:8000',
        internalRabbitmqWsUrl: process.env.INTERNAL_RABBITMQ_WS_URL || 'ws://localhost:15674/ws'
    };
}

// Load config at startup
const runtimeConfig = loadRuntimeConfig();

// CRITICAL: Set process.env from runtime config so Next.js API routes can access them
process.env.APP_ENV = runtimeConfig.appEnv || process.env.APP_ENV || 'production';
// NODE_ENV is set from the Kubernetes environment, not the runtime config.
// This is crucial for the Next.js server to start correctly with a standalone build.
process.env.INTERNAL_API_URL = runtimeConfig.internalApiUrl || process.env.INTERNAL_API_URL;
process.env.INTERNAL_RABBITMQ_WS_URL = runtimeConfig.internalRabbitmqWsUrl || process.env.INTERNAL_RABBITMQ_WS_URL;

const dev = process.env.NODE_ENV !== 'production';
const hostname = dev ? 'localhost' : '0.0.0.0';
const port = parseInt(process.env.PORT || '3000', 10);

// Initialize Next.js
const app = next({ dev, hostname, port });
const handle = app.getRequestHandler();

// Log configuration
console.log('Server configuration:');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('APP_ENV:', process.env.APP_ENV);
console.log('Internal API URL:', runtimeConfig.internalApiUrl);
console.log('Internal RabbitMQ WS URL:', runtimeConfig.internalRabbitmqWsUrl);
console.log('Public paths: /api → API proxy, /rabbitmq/ws → WebSocket proxy');

// Create a proxy server for WebSocket connections
const wsProxy = httpProxy.createProxyServer({
    ws: true,
    changeOrigin: true,
    // Timeout configurations
    proxyTimeout: 3600000, // 1 hour
    timeout: 3600000, // 1 hour
});

// Track retry attempts for WebSocket connections
const retryAttempts = new Map();

// Handle proxy errors with retry logic
wsProxy.on('error', function(err, req, res, socket) {
    const requestId = req.headers['sec-websocket-key'] || 'unknown';
    const attempts = retryAttempts.get(requestId) || 0;
    
    // Only log connection refused errors after all retries exhausted
    if (err.code === 'ECONNREFUSED') {
        if (attempts < 4) {
            // Transient error - don't log, will retry
            return;
        }
        console.error('[WebSocket] Connection refused after all retries:', {
            error: err.message,
            attempts: attempts,
            target: runtimeConfig.internalRabbitmqWsUrl
        });
    } else {
        // Log other errors immediately
        console.error('[WebSocket] Proxy error:', {
            error: err.message,
            code: err.code,
            url: req?.url,
            target: runtimeConfig.internalRabbitmqWsUrl
        });
    }
    
    // Clean up retry tracking
    retryAttempts.delete(requestId);
    
    if (res && res.writeHead && !res.headersSent) {
        res.writeHead(504, {
            'Content-Type': 'application/json'
        });
        res.end(JSON.stringify({
            error: 'Gateway Timeout',
            message: 'Failed to connect to RabbitMQ service'
        }));
    }
    
    // Close socket if available
    if (socket && !socket.destroyed) {
        socket.destroy();
    }
});

// Log successful WebSocket connections
wsProxy.on('open', function(proxySocket) {
    console.log('WebSocket connection opened to RabbitMQ');
});

wsProxy.on('close', function(res, socket, head) {
    console.log('WebSocket connection closed');
});

// Log WebSocket proxy requests
wsProxy.on('proxyReqWs', function(proxyReq, req, socket, options, head) {
    console.log('WebSocket proxy request:', {
        url: req.url,
        target: runtimeConfig.internalRabbitmqWsUrl,
        headers: req.headers
    });
    
    socket.on('error', function(err) {
        console.error('WebSocket socket error:', err);
    });
});

app.prepare().then(() => {
    const server = http.createServer(async (req, res) => {
        try {
            const parsedUrl = parse(req.url, true);
            await handle(req, res, parsedUrl);
        } catch (err) {
            console.error('Error occurred handling request:', {
                error: err.message,
                stack: err.stack,
                url: req.url,
                method: req.method
            });
            res.statusCode = 500;
            res.end('Internal Server Error');
        }
    });

    // Helper function to proxy WebSocket with retry logic
    function proxyWebSocketWithRetry(req, socket, head, targetUrl, attempt = 0) {
        const requestId = req.headers['sec-websocket-key'] || 'unknown';
        const maxRetries = 4;
        const baseDelay = 100; // Start with 100ms
        
        // Track attempt count
        retryAttempts.set(requestId, attempt);
        
        // Create a one-time error handler for this specific attempt
        const errorHandler = function(err) {
            if (err.code === 'ECONNREFUSED' && attempt < maxRetries) {
                // Calculate exponential backoff delay
                const delay = baseDelay * Math.pow(2, attempt);
                
                console.log(`[WebSocket] Connection refused, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
                
                // Retry after delay
                setTimeout(() => {
                    proxyWebSocketWithRetry(req, socket, head, targetUrl, attempt + 1);
                }, delay);
            } else {
                // Max retries reached or different error - let the main error handler deal with it
                // The error will bubble up to the wsProxy.on('error') handler
            }
        };
        
        // Remove any previous error listeners to avoid duplicates
        wsProxy.removeAllListeners('error');
        
        // Add error handler for this attempt
        wsProxy.once('error', errorHandler);
        
        // Attempt the proxy connection
        try {
            wsProxy.ws(req, socket, head, {
                target: targetUrl
            });
            
            // If successful, clean up retry tracking
            if (attempt > 0) {
                console.log(`[WebSocket] Connection successful after ${attempt} retries`);
            }
            retryAttempts.delete(requestId);
        } catch (err) {
            console.error('[WebSocket] Error initiating proxy:', err);
            socket.destroy();
            retryAttempts.delete(requestId);
        }
    }

    // Handle WebSocket upgrade requests
    server.on('upgrade', function (req, socket, head) {
        const parsedUrl = parse(req.url);
        
        // Proxy WebSocket connections to internal RabbitMQ service
        // Handle both direct path and ingress-prefixed path
        if (parsedUrl.pathname === '/rabbitmq/ws' || 
            parsedUrl.pathname === '/askaithena/rabbitmq/ws' ||
            parsedUrl.pathname.endsWith('/rabbitmq/ws')) {
            console.log('Upgrading WebSocket connection to internal RabbitMQ:', runtimeConfig.internalRabbitmqWsUrl);
            console.log('Original path:', parsedUrl.pathname);
            console.log('Headers:', req.headers);
            
            // Add error handler to socket before proxying
            socket.on('error', function(err) {
                console.error('Socket error during WebSocket upgrade:', err);
            });
            
            // The target should be the base URL without the /ws path
            // because the request already has /rabbitmq/ws which we'll rewrite to /ws
            const targetUrl = runtimeConfig.internalRabbitmqWsUrl.replace('/ws', '');
            
            // Rewrite the path from /rabbitmq/ws to /ws for RabbitMQ
            req.url = '/ws';
            
            console.log('Proxying WebSocket with rewritten path:', {
                originalPath: parsedUrl.pathname,
                newPath: req.url,
                target: targetUrl
            });
            
            // Forward the request to RabbitMQ with retry logic
            proxyWebSocketWithRetry(req, socket, head, targetUrl);
            console.log('WebSocket proxy initiated successfully');
        } else {
            console.log('Unknown WebSocket path:', parsedUrl.pathname);
            socket.destroy();
        }
    });

    server.listen(port, hostname, (err) => {
        if (err) throw err;
        console.log(`> Ready on http://${hostname}:${port}`);
        console.log('> Server-side proxy mode: Next.js proxies to internal services');
        console.log(`> Internal API URL: ${runtimeConfig.internalApiUrl}`);
        console.log(`> Internal RabbitMQ WebSocket URL: ${runtimeConfig.internalRabbitmqWsUrl}`);
        console.log('> Client uses fixed paths: /api and /rabbitmq/ws');
    });
});
