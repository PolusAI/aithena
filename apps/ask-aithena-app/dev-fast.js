// Fast development server - bypasses custom server.js for better performance
const { spawn } = require('child_process');

// Start Next.js directly without the custom server
const nextProcess = spawn('npx', ['next', 'dev', '--port', '3000'], {
  stdio: 'inherit',
  env: {
    ...process.env,
    // Force development mode
    NODE_ENV: 'development',
    // Disable telemetry for faster startup
    NEXT_TELEMETRY_DISABLED: '1'
  }
});

nextProcess.on('error', (err) => {
  console.error('Failed to start Next.js:', err);
  process.exit(1);
});

process.on('SIGINT', () => {
  nextProcess.kill('SIGINT');
  process.exit(0);
});
