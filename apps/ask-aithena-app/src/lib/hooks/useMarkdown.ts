import { useCallback, useMemo } from 'react';

/**
 * A hook that provides utilities for working with markdown content
 */
export const useMarkdown = () => {
    /**
     * Process markdown content to ensure proper formatting
     */
    const processMarkdown = useCallback((content: string): string => {
        if (!content) return '';

        // Don't modify line breaks, return content exactly as received from LLM
        return content;
    }, []);

    /**
     * Extract code blocks from markdown content
     */
    const extractCodeBlocks = useCallback((content: string): { language: string; code: string }[] => {
        const codeBlockRegex = /```([a-z]*)\n([\s\S]*?)```/g;
        const codeBlocks: { language: string; code: string }[] = [];

        let match;
        while ((match = codeBlockRegex.exec(content)) !== null) {
            const language = match[1] || 'text';
            const code = match[2].trim();
            codeBlocks.push({ language, code });
        }

        return codeBlocks;
    }, []);

    /**
     * Determine if content contains math equations
     */
    const containsMath = useCallback((content: string): boolean => {
        // Check for inline math: $equation$
        const inlineMathRegex = /\$[^\$\n]+\$/g;
        // Check for block math: $$equation$$
        const blockMathRegex = /\$\$[\s\S]+?\$\$/g;

        return inlineMathRegex.test(content) || blockMathRegex.test(content);
    }, []);

    return {
        processMarkdown,
        extractCodeBlocks,
        containsMath
    };
}; 