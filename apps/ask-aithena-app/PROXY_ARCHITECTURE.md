# Server-Side Proxy Architecture Guide

## Overview

The Ask Aithena App uses a **server-side proxy architecture** that allows you to use internal Kubernetes service names while still providing a seamless experience for browser clients.

## Architecture

```
┌─────────┐         ┌──────────────┐         ┌─────────────────┐
│ Browser │ ──────> │  Next.js App │ ──────> │ Internal        │
│         │ /api    │  (Proxy)     │         │ Services        │
│         │ /ws     │              │         │ (K8s cluster)   │
└─────────┘         └──────────────┘         └─────────────────┘
   Client              Server-Side              Backend
   (Public)            (Proxy Layer)            (Private)
```

### How It Works

1. **Browser makes requests** to Next.js app using relative paths:
   - API calls: `/api/ask`, `/api/health`, etc.
   - WebSocket: `/rabbitmq/ws`

2. **Next.js server proxies** these requests to internal services:
   - API calls → `http://ask-aithena-agent-service:8000`
   - WebSocket → `ws://rabbitmq-service:15674/ws`

3. **Internal services** are only accessible within the Kubernetes cluster

## Environment Variables

### Client-Side (NEXT_PUBLIC_*)

These are embedded in the browser bundle and must be accessible from the user's browser:

```bash
# What the browser sees
NEXT_PUBLIC_API_URL=/api
NEXT_PUBLIC_RABBITMQ_WS_URL=/rabbitmq/ws
```

### Server-Side (INTERNAL_*)

These are used by the Next.js server to connect to backend services:

```bash
# Where Next.js server connects
INTERNAL_API_URL=http://ask-aithena-agent-service:8000
INTERNAL_RABBITMQ_WS_URL=ws://rabbitmq-service:15674/ws
```

## Configuration Examples

### Local Development

```bash
# .env.local
NEXT_PUBLIC_API_URL=/api
NEXT_PUBLIC_RABBITMQ_WS_URL=/rabbitmq/ws
INTERNAL_API_URL=http://localhost:8000
INTERNAL_RABBITMQ_WS_URL=ws://localhost:15674/ws
```

### Kubernetes Deployment

```yaml
# ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: ask-aithena-app-config
data:
  # Client sees relative paths
  NEXT_PUBLIC_API_URL: "/api"
  NEXT_PUBLIC_RABBITMQ_WS_URL: "/rabbitmq/ws"
  
  # Server uses internal service names
  INTERNAL_API_URL: "http://ask-aithena-agent-service:8000"
  INTERNAL_RABBITMQ_WS_URL: "ws://rabbitmq-service:15674/ws"
```

## Benefits

### ✅ Security
- Backend services don't need to be exposed externally
- Only Next.js app needs to be accessible from outside the cluster
- Reduces attack surface

### ✅ Simplicity
- No need to configure ingress for every backend service
- No need for external URLs or DNS for backend services
- Works with internal Kubernetes service discovery

### ✅ Flexibility
- Easy to change backend service locations
- Can use different services in different environments
- No client-side code changes needed

### ✅ Performance
- Reduced latency (server-to-server communication within cluster)
- No additional network hops through ingress for backend calls

## How Proxy Works

### API Requests

API requests are handled by Next.js API routes that proxy to the internal service:

```typescript
// src/app/api/ask/route.ts
import { INTERNAL_API_URL } from '@/lib/server/config';

export async function POST(req: NextRequest) {
    // Proxy to internal service
    const response = await request(`${INTERNAL_API_URL}/ask`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
    
    return new NextResponse(response.body);
}
```

### WebSocket Connections

WebSocket connections are upgraded and proxied in `server.js`:

```javascript
// server.js
const wsProxy = httpProxy.createProxyServer({
    ws: true,
    target: process.env.INTERNAL_RABBITMQ_WS_URL
});

server.on('upgrade', function (req, socket, head) {
    if (req.url === '/rabbitmq/ws') {
        wsProxy.ws(req, socket, head);
    }
});
```

## Deployment Requirements

### 1. Next.js App Must Be Accessible

The Next.js app must be accessible from the browser. Options:

- **Ingress** (Recommended):
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  spec:
    rules:
    - host: askaithena.example.com
      http:
        paths:
        - path: /
          backend:
            service:
              name: ask-aithena-app-service
              port: 3000
  ```

- **NodePort**:
  ```yaml
  service:
    type: NodePort
    port: 80
    targetPort: 3000
    nodePort: 32136
  ```

- **LoadBalancer**:
  ```yaml
  service:
    type: LoadBalancer
    port: 80
    targetPort: 3000
  ```

### 2. Internal Services Must Be Accessible from Next.js Pod

Ensure internal services are accessible via Kubernetes service discovery:

```bash
# These should resolve from within the Next.js pod
nslookup ask-aithena-agent-service
nslookup rabbitmq-service
```

### 3. WebSocket Support

If using Ingress, ensure WebSocket support is enabled:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/websocket-services: "ask-aithena-app-service"
```

## Troubleshooting

### Issue: "INTERNAL_API_URL not set"

**Symptom:** App crashes on startup

**Solution:** Ensure ConfigMap includes all required variables:
```yaml
data:
  NEXT_PUBLIC_API_URL: "/api"
  NEXT_PUBLIC_RABBITMQ_WS_URL: "/rabbitmq/ws"
  INTERNAL_API_URL: "http://ask-aithena-agent-service:8000"
  INTERNAL_RABBITMQ_WS_URL: "ws://rabbitmq-service:15674/ws"
```

### Issue: "Failed to proxy to internal service"

**Symptom:** 504 Gateway Timeout errors

**Possible Causes:**
1. Internal service is down
2. Service name is incorrect
3. Network policy blocking traffic

**Debug:**
```bash
# Check if service exists
kubectl get svc ask-aithena-agent-service

# Check if pods are running
kubectl get pods -l app=ask-aithena-agent

# Test from Next.js pod
kubectl exec -it <next-pod> -- curl http://ask-aithena-agent-service:8000/health
```

### Issue: WebSocket connection fails

**Symptom:** "Failed to connect to RabbitMQ" in logs

**Possible Causes:**
1. RabbitMQ service is down
2. WebSocket port not exposed
3. Proxy configuration incorrect

**Debug:**
```bash
# Check RabbitMQ service
kubectl get svc rabbitmq-service

# Check if WebSocket port is exposed
kubectl get svc rabbitmq-service -o yaml | grep 15674

# Test WebSocket from Next.js pod
kubectl exec -it <next-pod> -- curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://rabbitmq-service:15674/ws
```

## Comparison with Direct Connection Mode

### Server-Side Proxy (Current)

**Pros:**
- Use internal service names
- Backend services don't need external exposure
- More secure
- Simpler networking

**Cons:**
- Next.js server is a single point of failure
- Slightly more complex server code
- All traffic goes through Next.js

### Direct Connection (Alternative)

**Pros:**
- Simpler Next.js code
- Direct browser-to-service communication
- No proxy overhead

**Cons:**
- Backend services must be externally accessible
- Requires ingress/routing for each service
- More complex networking setup
- Less secure (more services exposed)

## Migration from Direct Connection

If migrating from direct connection mode (v1.2.0), see `MIGRATION_SUMMARY.md` for details.

## Additional Resources

- [Kubernetes Deployment Guide](./KUBERNETES_DEPLOYMENT_GUIDE.md)
- [Environment Variables Sample](./.env.local.sample)
- [Helm Chart Configuration](../deployments/helm/ask-aithena/ask-aithena-chart/DEPLOYMENT_GUIDE.md)
