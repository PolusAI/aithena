/**
 * Secure Logger Utility
 * 
 * Security principles:
 * - Production: Minimal logging, no sensitive data
 * - Development: Helpful debugging with sanitized data
 * - No PII, tokens, or full request/response bodies in any environment
 */

type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

interface LogContext {
  [key: string]: any;
}

class SecureLogger {
  private isDevelopment: boolean;
  private serviceName: string;
  private sensitiveKeys = [
    'password', 'token', 'secret', 'key', 'authorization',
    'cookie', 'session', 'sessionId', 'query', 'history',
    'api_key', 'apiKey', 'access_token', 'refresh_token',
    'email', 'phone', 'ssn', 'credit_card'
  ];

  constructor(serviceName: string) {
    this.serviceName = serviceName;
    
    // Check both NODE_ENV and APP_ENV (from runtime config if available)
    let runtimeAppEnv = 'production';
    try {
      // Only try to get runtime config on client side
      if (typeof window !== 'undefined') {
        const getConfig = require('next/config').default;
        const { publicRuntimeConfig } = getConfig() || { publicRuntimeConfig: {} };
        runtimeAppEnv = publicRuntimeConfig.APP_ENV || 'production';
      } else {
        // On server side, use environment variable directly
        runtimeAppEnv = process.env.APP_ENV || 'production';
      }
    } catch (e) {
      // Fallback if getConfig fails
      runtimeAppEnv = process.env.APP_ENV || 'production';
    }
    
    this.isDevelopment = process.env.NODE_ENV === 'development' || runtimeAppEnv === 'development';
  }

  /**
   * Debug level - only logs in development
   */
  debug(message: string, context?: LogContext): void {
    if (this.isDevelopment) {
      const sanitized = this.sanitizeContext(context);
      console.log(this.formatMessage('DEBUG', message), sanitized);
    }
  }

  /**
   * Info level - logs in all environments with different detail levels
   */
  info(message: string, context?: LogContext): void {
    const sanitized = this.isDevelopment 
      ? this.sanitizeContext(context)
      : this.extractSafeMetadata(context);
    
    console.log(this.formatMessage('INFO', message), sanitized);
  }

  /**
   * Warning level - logs in all environments
   */
  warn(message: string, context?: LogContext): void {
    const sanitized = this.isDevelopment 
      ? this.sanitizeContext(context)
      : this.extractSafeMetadata(context);
    
    console.warn(this.formatMessage('WARN', message), sanitized);
  }

  /**
   * Error level - logs in all environments with stack traces only in dev
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorInfo: any = {};
    
    if (error instanceof Error) {
      errorInfo.name = error.name;
      errorInfo.message = this.sanitizeString(error.message);
      
      // Only include stack trace in development
      if (this.isDevelopment && error.stack) {
        // Limit stack trace to first 5 lines
        errorInfo.stack = error.stack.split('\n').slice(0, 5).join('\n');
      }
    } else if (error) {
      errorInfo.error = this.isDevelopment ? String(error) : 'An error occurred';
    }

    const sanitized = this.isDevelopment 
      ? this.sanitizeContext(context)
      : this.extractSafeMetadata(context);

    console.error(
      this.formatMessage('ERROR', message),
      { ...errorInfo, ...sanitized }
    );
  }

  /**
   * Format log message with timestamp and service name
   */
  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}] [${this.serviceName}] ${message}`;
  }

  /**
   * Sanitize context for development logging
   */
  private sanitizeContext(context?: LogContext): LogContext {
    if (!context) return {};

    const sanitized: LogContext = {};
    
    for (const [key, value] of Object.entries(context)) {
      // Check if key contains sensitive words
      if (this.isSensitiveKey(key)) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'string') {
        sanitized[key] = this.sanitizeString(value);
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeContext(value);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Extract only safe metadata for production
   */
  private extractSafeMetadata(context?: LogContext): LogContext {
    if (!context) return {};

    const safe: LogContext = {};
    const safeKeys = [
      'method', 'statusCode', 'duration', 'count', 'type',
      'action', 'resource', 'timestamp', 'version', 'environment'
    ];

    for (const [key, value] of Object.entries(context)) {
      if (safeKeys.includes(key) && !this.isSensitiveKey(key)) {
        safe[key] = value;
      }
    }

    return safe;
  }

  /**
   * Check if a key name suggests sensitive data
   */
  private isSensitiveKey(key: string): boolean {
    const lowerKey = key.toLowerCase();
    return this.sensitiveKeys.some(sensitive => 
      lowerKey.includes(sensitive)
    );
  }

  /**
   * Sanitize string values
   */
  private sanitizeString(value: string): string {
    // Truncate long strings
    if (value.length > 200) {
      return value.substring(0, 200) + '... [truncated]';
    }
    
    // Check for patterns that look like tokens or IDs
    if (this.looksLikeSensitiveData(value)) {
      return '[REDACTED]';
    }

    return value;
  }

  /**
   * Detect patterns that might be sensitive
   */
  private looksLikeSensitiveData(value: string): boolean {
    // JWT pattern
    if (/^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$/.test(value)) {
      return true;
    }
    
    // UUID pattern
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)) {
      return true;
    }
    
    // Long hex strings (potential tokens)
    if (/^[0-9a-f]{32,}$/i.test(value)) {
      return true;
    }

    return false;
  }
}

// Export singleton instances for different services
export const apiLogger = new SecureLogger('API');
export const wsLogger = new SecureLogger('WebSocket');
export const appLogger = new SecureLogger('App');

// Export the class for custom instances
export default SecureLogger;
