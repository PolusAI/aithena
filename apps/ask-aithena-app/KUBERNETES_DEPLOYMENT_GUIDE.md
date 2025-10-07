# Kubernetes Deployment Guide for Ask Aithena App

This guide explains how to deploy the Ask Aithena App in Kubernetes with the new direct connection architecture (no proxy dependencies).

## Architecture Overview

**NEW ARCHITECTURE (No Proxy):**
```
Browser → Backend Services (Direct)
```

The app no longer uses Next.js as a proxy. Instead:
- Client-side code connects directly to backend services
- All connections are configured via environment variables
- Works regardless of deployment URL/path

## Required Environment Variables

The application requires the following environment variables to be set in your Kubernetes ConfigMap:

### 1. `NEXT_PUBLIC_API_URL`
**Description:** The URL where the Ask Aithena Agent API is accessible from the browser.

**Example values:**
- Behind Ingress: `https://your-domain.com/api/aithena`
- NodePort: `http://your-cluster-ip:30000`
- LoadBalancer: `http://load-balancer-ip:8000`

**Important:** This must be a URL that the **browser** can access, not an internal Kubernetes service name.

### 2. `NEXT_PUBLIC_RABBITMQ_WS_URL`
**Description:** The WebSocket URL where RabbitMQ is accessible from the browser.

**Example values:**
- Behind Ingress: `wss://your-domain.com/rabbitmq/ws`
- NodePort: `ws://your-cluster-ip:30674`
- LoadBalancer: `ws://load-balancer-ip:15674/ws`

**Important:** 
- Use `wss://` for HTTPS deployments
- Use `ws://` for HTTP deployments
- This must be accessible from the **browser**, not just from within the cluster

## ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ask-aithena-app-config
  namespace: your-namespace
data:
  # API endpoint accessible from browser
  NEXT_PUBLIC_API_URL: "https://your-domain.com/api/aithena"
  
  # RabbitMQ WebSocket endpoint accessible from browser
  NEXT_PUBLIC_RABBITMQ_WS_URL: "wss://your-domain.com/rabbitmq/ws"
  
  # Optional: Application environment
  APP_ENV: "production"
  
  # Optional: Node environment
  NODE_ENV: "production"
```

## Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ask-aithena-app
  namespace: your-namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ask-aithena-app
  template:
    metadata:
      labels:
        app: ask-aithena-app
    spec:
      containers:
      - name: ask-aithena-app
        image: your-registry/ask-aithena-app:latest
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: ask-aithena-app-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Service Example

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ask-aithena-app-service
  namespace: your-namespace
spec:
  selector:
    app: ask-aithena-app
  ports:
  - port: 3000
    targetPort: 3000
    name: http
  type: ClusterIP
```

## Ingress Configuration

### Example with NGINX Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ask-aithena-ingress
  namespace: your-namespace
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    # WebSocket support
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/websocket-services: "rabbitmq-service"
spec:
  rules:
  - host: your-domain.com
    http:
      paths:
      # Next.js app
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ask-aithena-app-service
            port:
              number: 3000
      
      # Backend API (direct access)
      - path: /api/aithena
        pathType: Prefix
        backend:
          service:
            name: ask-aithena-agent-service
            port:
              number: 8000
      
      # RabbitMQ WebSocket (direct access)
      - path: /rabbitmq/ws
        pathType: Prefix
        backend:
          service:
            name: rabbitmq-service
            port:
              number: 15674
```

## Troubleshooting

### Application Won't Start

**Error:** `ERROR: Missing required environment variables`

**Solution:** Ensure your ConfigMap has `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_RABBITMQ_WS_URL` set.

**Verify:**
```bash
kubectl get configmap ask-aithena-app-config -n your-namespace -o yaml
```

### WebSocket Connection Fails

**Error:** `Failed to connect to RabbitMQ`

**Common causes:**
1. `NEXT_PUBLIC_RABBITMQ_WS_URL` is using an internal service name instead of external URL
2. Protocol mismatch (ws:// vs wss://)
3. Ingress not configured for WebSocket support
4. CORS issues

**Solution:**
- Verify the URL is accessible from your browser
- Check ingress annotations for WebSocket support
- Ensure protocol matches your deployment (wss:// for HTTPS sites)

### API Requests Fail

**Error:** Network errors when making API calls

**Common causes:**
1. `NEXT_PUBLIC_API_URL` points to internal service name
2. CORS not configured on backend
3. Ingress routing not set up correctly

**Solution:**
- Test the API URL directly in your browser
- Verify ingress routing rules
- Check backend CORS configuration

## Deployment Checklist

- [ ] ConfigMap created with correct environment variables
- [ ] Environment variables use externally accessible URLs (not internal service names)
- [ ] Protocol matches deployment (ws:// or wss://, http:// or https://)
- [ ] Ingress configured with WebSocket support annotations
- [ ] Backend services are exposed via Ingress or NodePort/LoadBalancer
- [ ] CORS configured on backend to allow requests from app domain
- [ ] SSL certificates configured if using HTTPS/WSS

## Migration from Old Proxy-Based Architecture

If you're migrating from the old proxy-based setup:

1. **Remove proxy dependencies:** The app no longer needs proxy configuration
2. **Update ConfigMap:** Add `NEXT_PUBLIC_` prefixed variables
3. **Configure Ingress:** Set up direct routing to backend services
4. **Test connectivity:** Verify browser can access backend URLs directly
5. **Deploy updated app:** New version doesn't use proxy logic

## Testing the Deployment

1. **Check pod logs:**
   ```bash
   kubectl logs -f deployment/ask-aithena-app -n your-namespace
   ```
   
   Look for:
   ```
   ✓ All required environment variables are set
   > Ready on http://0.0.0.0:3000
   > Direct connection mode: Client connects directly to backend services
   ```

2. **Test from browser console:**
   ```javascript
   // Check API connection
   fetch(process.env.NEXT_PUBLIC_API_URL + '/health')
   
   // Check environment variables
   console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)
   console.log('RabbitMQ URL:', process.env.NEXT_PUBLIC_RABBITMQ_WS_URL)
   ```

3. **Verify WebSocket connection:**
   - Open browser DevTools → Network tab
   - Filter by "WS" (WebSocket)
   - Submit a question
   - Verify WebSocket connection is established to the correct URL

## Security Considerations

1. **Use HTTPS/WSS in production:** Always use secure protocols for production deployments
2. **Configure CORS properly:** Restrict backend CORS to your app's domain only
3. **Use network policies:** Implement Kubernetes network policies to control traffic
4. **Secret management:** Consider using Kubernetes Secrets for sensitive configuration
5. **Rate limiting:** Implement rate limiting on ingress/backend

## Additional Resources

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [NGINX Ingress WebSocket](https://kubernetes.github.io/ingress-nginx/user-guide/miscellaneous/#websockets)
