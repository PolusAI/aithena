#!/bin/bash

# Clean up node_modules
rm -rf node_modules
rm -rf .next

# Install dependencies
npm install

# Install specific versions of React packages
npm install react@latest react-dom@latest

# Install ESLint and related packages
npm install --save-dev \
  eslint@latest \
  eslint-config-next@latest \
  @eslint/object-schema@latest \
  @eslint/config-array@latest

# Install newer versions of deprecated packages
npm install --save-dev rimraf@latest glob@latest

# Create necessary type declaration files
mkdir -p src/types

echo "Setup completed successfully! Run 'npm run dev' to start the development server." 