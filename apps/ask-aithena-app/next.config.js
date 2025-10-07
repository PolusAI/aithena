/** @type {import('next').NextConfig} */

const nextConfig = {
    reactStrictMode: true,
    swcMinify: true,
    output: 'standalone',
    // Optimize for development
    onDemandEntries: {
        // period (in ms) where the server will keep pages in the buffer
        maxInactiveAge: 25 * 1000,
        // number of pages that should be kept simultaneously without being disposed
        pagesBufferLength: 2,
    },
    // Disable source maps in development for faster builds
    productionBrowserSourceMaps: false,
    webpack: (config, { dev, isServer }) => {
        // Don't override devtool in development to avoid performance issues
        return config;
    },
    // Public runtime configuration - accessible on both client and server
    publicRuntimeConfig: {
        API_URL: process.env.NEXT_PUBLIC_API_URL,
        RABBITMQ_WS_URL: process.env.NEXT_PUBLIC_RABBITMQ_WS_URL,
        APP_ENV: process.env.APP_ENV || 'production',
    },
    // Environment variables with NEXT_PUBLIC_ prefix are automatically available to the browser
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
        NEXT_PUBLIC_RABBITMQ_WS_URL: process.env.NEXT_PUBLIC_RABBITMQ_WS_URL,
    }
};

module.exports = nextConfig;
