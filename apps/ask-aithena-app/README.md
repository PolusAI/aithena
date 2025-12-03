# Ask Aithena Web App

A modern Next.js web interface for the Ask Aithena chatbot system.

## Features

- Next.js 14+ with App Router
- Tailwind CSS v4 for styling
- TypeScript for type safety
- Three AI modes: Owl, Shield, and Aegis
- Real-time feedback via RabbitMQ
- Streaming responses
- Responsive design with dark mode

## Prerequisites

- Node.js 18+ and npm/yarn
- Running FastAPI backend for Ask Aithena
- RabbitMQ instance for real-time updates

## Environment Setup

1. Copy `.env.local` or create your own with the following variables:

```
API_URL=http://localhost:8000  # URL to your FastAPI backend
RABBITMQ_WS_URL=ws://localhost:15674/ws  # WebSocket URL for RabbitMQ
```

## Installation

```bash
# Install dependencies
npm install
# or
yarn install

# Run development server
npm run dev
# or
yarn dev
```

## Development

The application will start at [http://localhost:3000](http://localhost:3000).

## Build for Production

```bash
# Build the application
npm run build
# or
yarn build

# Start the production server
npm start
# or
yarn start
```

## Docker Deployment

Build and run the Docker container:

```bash
# Build the Docker image
docker build -t ask-aithena-app .

# Run the container
docker run -p 3000:3000 ask-aithena-app
```

## Project Structure

- `/src/app` - Next.js App Router pages
- `/src/components` - React components
- `/src/services` - API and RabbitMQ services
- `/src/store` - State management with Zustand
- `/src/lib` - Utility functions and types

## Env Var

`ASK_AITHENA_API_URL` *Optional*: default is "http://localhost:8080". Ask Aithena URL.
`ASK_AITHENA_STREAM` *Optional*: default is True. If True, response from Ask Aithena will be streamed. If False, the entire response will be shown once the entire response is available.

## Deployment

Ask-aithena agent needs to be deployed as it is our backend. 
See [instructions](../../agents/ask-aithena-agent/README.md)

## Test 

Create a tunnel to your host

```shell
ssh -L ${NODE_PORT}:127.0.0.1:${NODE_PORT} ${USER}@{REMOTE_HOST}
```

Browse to `http://localhost:${NODE_PORT}`

Ask Aithena!

## Next Steps
- Integrate with login (auth)
- Add a copy button to the response
- Add a regenerate button to the response
- Add edit message button to inputs
- Support for multiple models
- Support for message history