/**
 * Server-side environment variable access
 * This file is used for server components and server-side operations
 */

export const getServerEnv = () => {
  return {
    API_URL: process.env.NEXT_PUBLIC_API_URL,
    RABBITMQ_WS_URL: process.env.NEXT_PUBLIC_RABBITMQ_WS_URL,
  };
}; 