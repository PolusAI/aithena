// Module declarations for libraries without type definitions
declare module 'zustand' {
    export function create<T>(initializer: (set: any, get: any, api: any) => T): (selector?: any, equalityFn?: any) => T;
}

declare module 'rehype-highlight' {
    const rehypeHighlight: any;
    export default rehypeHighlight;
}

declare module 'rehype-katex' {
    const rehypeKatex: any;
    export default rehypeKatex;
}

declare module 'remark-gfm' {
    const remarkGfm: any;
    export default remarkGfm;
}

declare module 'remark-math' {
    const remarkMath: any;
    export default remarkMath;
}

declare module 'framer-motion' {
    export const motion: any;
    export const AnimatePresence: any;
}

declare module 'react-markdown' {
    import { FC } from 'react';
    const ReactMarkdown: FC<any>;
    export default ReactMarkdown;
}

// Global type extensions
declare namespace JSX {
    interface IntrinsicElements {
        [key: string]: any;
    }
}

// Make sure window types are consistent
declare interface Window {
    ENV?: Record<string, string>;
    WebSocket: typeof WebSocket;
}

// Extend Response for streaming
interface ReadableStreamDefaultReader<R = any> {
    read(): Promise<{ done: boolean; value: R }>;
    releaseLock(): void;
}

interface Response {
    body?: {
        getReader(): ReadableStreamDefaultReader<Uint8Array>;
    };
} 