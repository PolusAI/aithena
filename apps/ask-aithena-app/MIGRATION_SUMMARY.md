# Migration Summary: Removing Hardcoded Services and Proxy Dependencies

## Overview

This migration removes all hardcoded service names ('rabbitmq-service', 'ask-aithena-agent-service') and eliminates the proxy-based architecture in favor of direct connections from the browser to backend services.

## What Changed

### 1. **Removed Proxy Logic**
- **File:** `server.js`
- **Changes:**
  - Removed all `http-proxy` code
  - Removed WebSocket upgrade handling
  - Removed API request proxying
  - Added environment variable validation at startup

### 2. **Removed Hardcoded Fallbacks**
- **File:** `src/lib/server/config.ts`
- **Changes:**
  - Removed fallback to `'http://ask-aithena-agent-service:8000'`
  - Removed fallback to `'ws://rabbitmq-service:15674/ws'`
  - Added validation that throws errors if environment variables are missing

### 3. **Updated Next.js Configuration**
- **File:** `next.config.js`
- **Changes:**
  - Removed `rewrites()` function (no more proxy routing)
  - Simplified configuration to only handle environment variables

### 4. **Updated Client-Side WebSocket Connection**
- **File:** `src/services/rabbitmq.ts`
- **Changes:**
  - Now reads WebSocket URL directly from environment variable
  - Connects directly to RabbitMQ (no proxy)
  - Removed server-side config fetching

### 5. **Updated Environment Variables**
- **Old variables (server-side only):**
  - `API_URL`
  - `RABBITMQ_WS_URL`

- **New variables (client-side accessible):**
  - `NEXT_PUBLIC_API_URL` (required)
  - `NEXT_PUBLIC_RABBITMQ_WS_URL` (required)

## Architecture Change

### Before (Proxy-Based)
```
Browser → Next.js Server → Backend Services
         (proxy layer)
```

### After (Direct Connection)
```
Browser → Backend Services
         (direct)
```

## Benefits

1. **No Proxy Dependencies:** Simpler architecture, fewer points of failure
2. **Works Anywhere:** Not dependent on specific URL paths or proxy configuration
3. **Better Performance:** Direct connections eliminate proxy overhead
4. **Easier Debugging:** Clear error messages, direct connection issues
5. **More Flexible:** Works with any ingress/routing configuration

## Breaking Changes

### For Kubernetes Deployments

**You MUST update your ConfigMap** to include the new environment variables with externally accessible URLs.

**Old ConfigMap (will not work):**
```yaml
data:
  API_URL: "http://ask-aithena-agent-service:8000"
  RABBITMQ_WS_URL: "ws://rabbitmq-service:15674/ws"
```

**New ConfigMap (required):**
```yaml
data:
  NEXT_PUBLIC_API_URL: "https://your-domain.com/api/aithena"
  NEXT_PUBLIC_RABBITMQ_WS_URL: "wss://your-domain.com/rabbitmq/ws"
```

### For Local Development

**Old `.env.local` (will not work):**
```bash
API_URL=http://localhost:8000
RABBITMQ_WS_URL=ws://localhost:15674/ws
```

**New `.env.local` (required):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RABBITMQ_WS_URL=ws://localhost:15674/ws
```

## Migration Steps

### Step 1: Update Your ConfigMap

```bash
# Edit your ConfigMap
kubectl edit configmap ask-aithena-app-config -n your-namespace

# Or apply a new ConfigMap
kubectl apply -f updated-configmap.yaml
```

Example updated ConfigMap:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ask-aithena-app-config
  namespace: your-namespace
data:
  NEXT_PUBLIC_API_URL: "https://your-domain.com/api/aithena"
  NEXT_PUBLIC_RABBITMQ_WS_URL: "wss://your-domain.com/rabbitmq/ws"
  APP_ENV: "production"
  NODE_ENV: "production"
```

### Step 2: Ensure Ingress Routes Backend Services

Your Ingress must expose both the API and RabbitMQ WebSocket to the browser.

Example Ingress configuration:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ask-aithena-ingress
  annotations:
    nginx.ingress.kubernetes.io/websocket-services: "rabbitmq-service"
spec:
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        backend:
          service:
            name: ask-aithena-app-service
            port: 3000
      - path: /api/aithena
        backend:
          service:
            name: ask-aithena-agent-service
            port: 8000
      - path: /rabbitmq/ws
        backend:
          service:
            name: rabbitmq-service
            port: 15674
```

### Step 3: Deploy Updated Application

```bash
# Restart the deployment to pick up new ConfigMap
kubectl rollout restart deployment/ask-aithena-app -n your-namespace

# Watch the rollout
kubectl rollout status deployment/ask-aithena-app -n your-namespace
```

### Step 4: Verify Deployment

```bash
# Check logs for successful startup
kubectl logs -f deployment/ask-aithena-app -n your-namespace
```

Look for:
```
✓ All required environment variables are set
> Ready on http://0.0.0.0:3000
> Direct connection mode: Client connects directly to backend services
> API URL: https://your-domain.com/api/aithena
> RabbitMQ WebSocket URL: wss://your-domain.com/rabbitmq/ws
```

### Step 5: Test in Browser

1. Open the application
2. Open browser DevTools → Console
3. Check environment variables:
   ```javascript
   console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)
   console.log('RabbitMQ URL:', process.env.NEXT_PUBLIC_RABBITMQ_WS_URL)
   ```
4. Submit a question and verify WebSocket connection in Network tab

## Troubleshooting

### Application Won't Start

**Symptom:** Pod crashes or restarts continuously

**Error in logs:**
```
ERROR: Missing required environment variables:
  - NEXT_PUBLIC_API_URL
  - NEXT_PUBLIC_RABBITMQ_WS_URL
```

**Solution:** Update ConfigMap with the new variable names and restart deployment.

### WebSocket Connection Fails

**Symptom:** "Failed to connect to RabbitMQ" in browser console

**Common Causes:**
1. Using internal service name instead of external URL
2. Protocol mismatch (ws:// vs wss://)
3. Ingress not configured for WebSocket

**Solution:** 
- Verify URL in browser console
- Test WebSocket URL directly: `wscat -c wss://your-domain.com/rabbitmq/ws`
- Check Ingress annotations

### API Calls Fail

**Symptom:** Network errors, CORS errors

**Common Causes:**
1. API URL not externally accessible
2. CORS not configured on backend
3. Ingress routing incorrect

**Solution:**
- Test API URL: `curl https://your-domain.com/api/aithena/health`
- Verify Ingress routes
- Check backend CORS configuration

## Rollback Plan

If you need to rollback to the old version:

1. **Restore old ConfigMap:**
   ```bash
   kubectl apply -f old-configmap.yaml
   ```

2. **Deploy old version:**
   ```bash
   kubectl set image deployment/ask-aithena-app \
     ask-aithena-app=your-registry/ask-aithena-app:old-version
   ```

3. **Verify rollback:**
   ```bash
   kubectl rollout status deployment/ask-aithena-app
   ```

## Additional Documentation

- **Full deployment guide:** See `KUBERNETES_DEPLOYMENT_GUIDE.md`
- **Environment variables:** See `.env.local.sample`
- **Troubleshooting:** See `KUBERNETES_DEPLOYMENT_GUIDE.md` → Troubleshooting section

## Support

If you encounter issues:
1. Check pod logs: `kubectl logs -f deployment/ask-aithena-app`
2. Verify ConfigMap: `kubectl get configmap ask-aithena-app-config -o yaml`
3. Test URLs directly from your browser
4. Check Ingress configuration: `kubectl describe ingress ask-aithena-ingress`
