import getConfig from 'next/config';

// This works at runtime, not build time
export function getRuntimeConfig() {
  const { publicRuntimeConfig, serverRuntimeConfig } = getConfig() || {};
  
  return {
    public: publicRuntimeConfig || {},
    server: serverRuntimeConfig || {},
    
    // Helper methods
    isDevMode(): boolean {
      return publicRuntimeConfig?.APP_ENV === 'development';
    },
    
    getAppEnv(): string {
      return publicRuntimeConfig?.APP_ENV || 'production';
    }
  };
}
