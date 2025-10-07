/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  
  // Runtime configuration - BEST PRACTICE
  publicRuntimeConfig: {
    APP_ENV: process.env.APP_ENV || 'production',
    // Add other runtime variables here
  },
  
  // Server-only runtime configuration
  serverRuntimeConfig: {
    // Server-only secrets go here
    INTERNAL_API_URL: process.env.INTERNAL_API_URL,
  },
}

module.exports = nextConfig
