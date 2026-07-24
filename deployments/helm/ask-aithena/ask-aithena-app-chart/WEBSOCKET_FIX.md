# WebSocket Connection Fix

## Problem
The browser was unable to connect to RabbitMQ WebSocket, showing the error:
```
WebSocket connection to 'ws://localhost:32136/rabbitmq/ws' failed: 
WebSocket is closed before the connection is established.
```

## Root Cause
The runtime ConfigMap (`runtime-configmap.yaml`) was missing the `rabbitmqWsUrl` field that the client-side code needs. Without this field, the API config route would fall back to the environment variable, but the client-side code in `rabbitmq.ts` needs this value to construct the WebSocket URL properly.

## Solution
Added `rabbitmqWsUrl: "/rabbitmq/ws"` to the runtime ConfigMap. This tells the client to use the relative path `/rabbitmq/ws`, which:

1. The browser converts to the full URL (e.g., `ws://localhost:32136/rabbitmq/ws`)
2. Connects to the Next.js server on port 32136 (NodePort)
3. Gets proxied by the custom server (`server.js`) to the internal RabbitMQ service
4. **No ingress or external proxy needed** - everything stays within the Kubernetes cluster

## Architecture
```
Browser → ws://localhost:32136/rabbitmq/ws
         ↓
Next.js Server (ask-aithena-app) on port 32136
         ↓ (WebSocket proxy in server.js)
RabbitMQ Internal Service: ws://ask-aithena-rabbitmq-chart-internal:15674/ws
```

This mirrors how API calls work:
```
Browser → http://localhost:32136/api/ask
         ↓
Next.js Server (ask-aithena-app) on port 32136
         ↓ (HTTP proxy in Next.js API routes)
Agent Internal Service: http://ask-aithena-ask-aithena-agent-chart-service:8000
```

## Files Changed
- `deployments/helm/ask-aithena/ask-aithena-app-chart/templates/runtime-configmap.yaml`
  - Added `"rabbitmqWsUrl": "/rabbitmq/ws"` to the runtime.json data

## Deployment Steps

### 1. Update the Helm Chart
The chart has already been updated. You need to rebuild and redeploy.

### 2. Rebuild the Chart Dependencies (if needed)
```bash
cd deployments/helm/ask-aithena/ask-aithena-chart
mk helm dependency update
```

### 3. Upgrade the Deployment
```bash
mk helm upgrade ask-aithena ./ask-aithena-chart \
  --namespace askaithena \
  --values ./ask-aithena-chart/values.yaml
```

### 4. Verify the ConfigMap
```bash
mkk -n askaithena get configmap ask-aithena-ask-aithena-app-chart-runtime -o yaml
```

You should see:
```yaml
data:
  runtime.json: |
    {
      "appEnv": "development",
      "nodeEnv": "production",
      "internalApiUrl": "http://ask-aithena-ask-aithena-agent-chart-service:8000",
      "internalRabbitmqWsUrl": "ws://ask-aithena-rabbitmq-chart-internal:15674/ws",
      "rabbitmqWsUrl": "/rabbitmq/ws"
    }
```

### 5. Restart the App Pods
The ConfigMap is mounted as a volume, so you need to restart the pods to pick up the change:
```bash
mkk -n askaithena rollout restart deployment ask-aithena-ask-aithena-app-chart
```

### 6. Verify the Fix
1. Wait for pods to be ready:
   ```bash
   mkk -n askaithena get pods -l app.kubernetes.io/name=ask-aithena-app-chart
   ```

2. Check the logs to confirm the config is loaded:
   ```bash
   mkk -n askaithena logs -l app.kubernetes.io/name=ask-aithena-app-chart --tail=50
   ```
   
   Look for:
   ```
   ✓ Runtime config loaded from: /app/config/runtime.json
   ```

3. Open the app in your browser and check the console. The WebSocket connection should now succeed.

## Testing
After deployment, you should see in the browser console:
```
Connected to STOMP broker
```

Instead of:
```
WebSocket connection to 'ws://localhost:32136/rabbitmq/ws' failed
```

## Notes
- The WebSocket proxy is already implemented in `server.js` (lines 113-135)
- The API config route already handles `rabbitmqWsUrl` (line 48 in `route.ts`)
- No changes to application code were needed - only the Helm configuration
- This solution keeps all communication internal to the Kubernetes cluster
- The browser only needs to reach the Next.js NodePort (32136)
