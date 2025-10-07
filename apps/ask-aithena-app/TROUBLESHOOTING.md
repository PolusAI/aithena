# Troubleshooting Guide

## Common TypeScript Errors and Solutions

### "Cannot find module 'react' or its corresponding type declarations."

**Solution:**
1. Make sure the React types are properly installed:
   ```bash
   npm install --save-dev @types/react @types/react-dom
   ```
2. Ensure proper imports in your components:
   ```tsx
   import React, { useState, useEffect } from 'react';
   ```

### "JSX element implicitly has type 'any' because no interface 'JSX.IntrinsicElements' exists"

**Solution:**
This error happens when TypeScript can't find the JSX type definitions. It's fixed by:

1. Having the JSX namespace properly declared in your global.d.ts:
   ```ts
   declare namespace JSX {
     interface IntrinsicElements {
       [key: string]: any;
     }
   }
   ```
2. Using the correct tsconfig.json settings:
   ```json
   {
     "compilerOptions": {
       "jsx": "preserve",
       // other options...
     }
   }
   ```

### "Module '"zustand"' has no exported member 'create'"

**Solution:**
Add a proper type declaration for the module in global.d.ts:
```ts
declare module 'zustand' {
  export function create<T>(initializer: (set: any, get: any, api: any) => T): (selector?: any, equalityFn?: any) => T;
}
```

### "Cannot find name 'process'. Do you need to install type definitions for node?"

**Solution:**
1. Install Node.js types:
   ```bash
   npm install --save-dev @types/node
   ```
2. Or create a safe wrapper for accessing environment variables:
   ```ts
   const getEnv = (key: string, defaultValue: string = ''): string => {
     if (typeof process !== 'undefined' && process.env) {
       return process.env[key] || defaultValue;
     }
     return defaultValue;
   };
   ```

## Building the Project

If you encounter build errors:

1. Clean your project:
   ```bash
   rm -rf node_modules .next
   npm install
   ```

2. Update dependencies to non-deprecated versions:
   ```bash
   npm install eslint@latest rimraf@latest glob@latest
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

Remember to check the console for any runtime errors that might not be caught by TypeScript. 