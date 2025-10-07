'use client';

import React, { FC, useEffect, useState, useRef, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Message } from '@/lib/types';
import { useMarkdown } from '@/lib/hooks/useMarkdown';

// Define reference type
interface Reference {
    index: number;
    title: string;
    authors: string[];
    year: string | number;
    doi: string;
    id: string;
    score: number | null;
}

interface MessageItemProps {
    message: Message;
    sharedReferences?: string | null;
    onShowTooltip?: (ref: any, x: number, y: number) => void;
    onHideTooltip?: () => void;
    onHideTooltipImmediately?: () => void;
}

const MessageItem: FC<MessageItemProps> = ({ 
    message, 
    sharedReferences,
    onShowTooltip,
    onHideTooltip,
    onHideTooltipImmediately
}) => {
    const isUser = message.role === 'user';
    const [mounted, setMounted] = useState(false);
    const { processMarkdown } = useMarkdown();
    const [references, setReferences] = useState<Reference[]>([]);
    const messageContentRef = useRef<HTMLDivElement>(null);
    
    // Determine if this is a new message (less than 2 seconds old)
    const isNewMessage = useRef(false);
    
    useEffect(() => {
        // Check if message was created recently (within 2 seconds)
        if (message.timestamp) {
            const messageTime = new Date(message.timestamp).getTime();
            const currentTime = new Date().getTime();
            isNewMessage.current = (currentTime - messageTime) < 2000;
        } else {
            // If no timestamp, assume it's not new (existing message)
            isNewMessage.current = false;
        }
        
        setMounted(true);

        // Parse references when component mounts
        if (!isUser) {
            // Use message references if available, otherwise use shared references
            const referencesToParse = message.references || sharedReferences;
            if (referencesToParse) {
                try {
                    const refs = JSON.parse(referencesToParse) as Reference[];
                    setReferences(refs);
                } catch (e) {
                    console.error("Failed to parse references:", e);
                }
            }
        }
    }, [message.references, isUser, message.timestamp, sharedReferences]);
    
    // Create a map of reference indexes for quick lookup
    const refMap = useMemo(() => {
        return new Map(references.map(ref => [ref.index.toString(), ref]));
    }, [references]);
    
    // Custom text renderer that processes citations
    const renderTextWithCitations = useCallback((text: string) => {
        if (!text || isUser) return text;
        
        // Combined regex for both patterns - now also catches citations with spaces
        const combinedRegex = /\(\s*(\d+(?:\s*,\s*\d+)*)\s*\)/g;
        const parts: (string | React.ReactElement)[] = [];
        let lastIndex = 0;
        let match;
        let keyIndex = 0;
        
        while ((match = combinedRegex.exec(text)) !== null) {
            const fullMatch = match[0];  // e.g. "(1)" or "(1, 4, 9)" or "( 1 )"
            const citationContent = match[1]; // e.g. "1" or "1, 4, 9"
            const matchIndex = match.index;
            
            // Add text before the citation
            if (matchIndex > lastIndex) {
                parts.push(text.substring(lastIndex, matchIndex));
            }
            
            // Check if this is a grouped citation or individual citation
            if (citationContent.includes(',')) {
                // Grouped citation like (1, 4, 9)
                const citationNumbers = citationContent.split(',').map(n => n.trim());
                const groupElements: React.ReactElement[] = [<span key={`group-open-${keyIndex++}`}>(</span>];
                
                citationNumbers.forEach((num, idx) => {
                    const ref = refMap.get(num);
                    
                    groupElements.push(
                        <span
                            key={`citation-${keyIndex++}`}
                            className="citation-ref"
                            data-citation-id={num}
                            onMouseEnter={(e) => {
                                if (ref && onShowTooltip) {
                                    const rect = e.currentTarget.getBoundingClientRect();
                                    onShowTooltip(ref, rect.right + 5, rect.top);
                                }
                            }}
                            onMouseLeave={() => {
                                if (onHideTooltip) {
                                    onHideTooltip();
                                }
                            }}
                            onClick={() => {
                                if (ref && onHideTooltipImmediately) {
                                    onHideTooltipImmediately();
                                    handleCitationClick(ref);
                                }
                            }}
                            style={{ cursor: ref ? 'pointer' : 'default' }}
                        >
                            {num}
                        </span>
                    );
                    
                    if (idx < citationNumbers.length - 1) {
                        groupElements.push(<span key={`comma-${keyIndex++}`}>, </span>);
                    }
                });
                
                groupElements.push(<span key={`group-close-${keyIndex++}`}>)</span>);
                
                parts.push(
                    <span key={`group-${keyIndex++}`} className="citation-group">
                        {groupElements}
                    </span>
                );
            } else {
                // Individual citation like (1)
                const citationNumber = citationContent;
                const ref = refMap.get(citationNumber);
                
                parts.push(
                    <span
                        key={`citation-${keyIndex++}`}
                        className="citation-ref"
                        data-citation-id={citationNumber}
                        onMouseEnter={(e) => {
                            if (ref && onShowTooltip) {
                                const rect = e.currentTarget.getBoundingClientRect();
                                onShowTooltip(ref, rect.right + 5, rect.top);
                            }
                        }}
                        onMouseLeave={() => {
                            if (onHideTooltip) {
                                onHideTooltip();
                            }
                        }}
                        onClick={() => {
                            if (ref && onHideTooltipImmediately) {
                                onHideTooltipImmediately();
                                handleCitationClick(ref);
                            }
                        }}
                        style={{ cursor: ref ? 'pointer' : 'default' }}
                    >
                        {fullMatch}
                    </span>
                );
            }
            
            lastIndex = matchIndex + fullMatch.length;
        }
        
        // Add any remaining text
        if (lastIndex < text.length) {
            parts.push(text.substring(lastIndex));
        }
        
        // If no citations were found, return the original text
        if (parts.length === 0) {
            return text;
        }
        
        return <>{parts}</>;
    }, [isUser, refMap, onShowTooltip, onHideTooltip, onHideTooltipImmediately]);
    
    // Handle citation click
    const handleCitationClick = useCallback((ref: Reference) => {
        const detailsElement = document.querySelector('.references-content')?.parentElement;
        if (detailsElement && detailsElement instanceof HTMLDetailsElement) {
            // Open the details if it's closed
            if (!detailsElement.open) {
                detailsElement.open = true;
            }
            
            // Wait a tiny bit for the details to expand
            setTimeout(() => {
                // Find the reference element by index
                const refElement = document.querySelector(`.reference-item[data-ref-index="${ref.index}"]`);
                if (refElement) {
                    // Scroll the reference into view with smooth behavior
                    refElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    // Add a temporary highlight effect
                    refElement.classList.add('highlight-reference');
                    setTimeout(() => {
                        refElement.classList.remove('highlight-reference');
                    }, 2000);
                }
            }, 50);
        }
    }, []);

    // Don't render until client-side
    if (!mounted) return null;

    return (
        <motion.div
            initial={isNewMessage.current ? { opacity: 0, y: 10 } : { opacity: 1, y: 0 }}
            animate={{ opacity: 1, y: 0 }}
            transition={isNewMessage.current ? { duration: 0.4, ease: "easeOut" } : { duration: 0 }}
            className="mb-8 w-full"
            layout={false}
        >
            <div className="px-4">
                <motion.div
                    initial={isNewMessage.current ? { opacity: 0, x: isUser ? 20 : -20 } : { opacity: 1, x: 0 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={isNewMessage.current ? { delay: 0.1 } : { duration: 0 }}
                    className={`text-base font-medium mb-2 text-gray-700 dark:text-gray-300 flex items-baseline gap-2 ${isUser ? 'justify-end' : ''}`}
                    layout={false}
                >
                    {isUser ? (
                        <>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                            <span>You</span>
                        </>
                    ) : (
                        <>
                            <span>Aithena</span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </>
                    )}
                </motion.div>

                <div className={`flex ${isUser ? 'justify-end' : ''}`}>
                    <motion.div
                        initial={isNewMessage.current ? { opacity: 0, y: 10 } : { opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={isNewMessage.current ? { delay: 0.2 } : { duration: 0 }}
                        layout={false}
                        className={`p-5 rounded-2xl ${isUser
                            ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white shadow-lg inline-block max-w-[85%]'
                            : 'bg-white dark:bg-gray-800/80 text-gray-800 dark:text-gray-100 shadow-lg shadow-gray-500/10 dark:shadow-gray-900/20 border border-gray-100 dark:border-gray-700'
                            }`}
                    >
                        <div
                            ref={messageContentRef}
                            className={`${isUser ? 'text-gray-900 dark:text-white text-right' : 'text-gray-800 dark:text-gray-100'}`}
                            onMouseLeave={() => {
                                // Ensure tooltip is hidden when mouse leaves the message area
                                if (onHideTooltip) {
                                    onHideTooltip();
                                }
                            }}
                        >
                            <ReactMarkdown
                                rehypePlugins={[rehypeHighlight, rehypeKatex]}
                                remarkPlugins={[remarkGfm, remarkMath]}
                                className={`prose dark:prose-invert max-w-none text-base break-words ${isUser ? '!text-gray-900 dark:!text-white prose-headings:text-gray-900 dark:prose-headings:text-white prose-strong:text-gray-900 dark:prose-strong:text-white prose-code:text-gray-900 dark:prose-code:text-white' : ''} markdown-content`}
                                components={{
                                    h1: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h1 className="text-3xl font-bold mt-8 mb-4 first:mt-0 text-gray-900 dark:text-gray-100 leading-tight tracking-tight" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h1>
                                    ),
                                    h2: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h2 className="text-2xl font-semibold mt-6 mb-3 text-gray-900 dark:text-gray-100 leading-tight tracking-tight" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h2>
                                    ),
                                    h3: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h3 className="text-xl font-semibold mt-5 mb-2.5 text-gray-900 dark:text-gray-100 leading-snug" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h3>
                                    ),
                                    h4: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h4 className="text-lg font-medium mt-4 mb-2 text-gray-900 dark:text-gray-100 leading-snug" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h4>
                                    ),
                                    h5: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h5 className="text-base font-medium mt-3 mb-2 text-gray-900 dark:text-gray-100" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h5>
                                    ),
                                    h6: ({ children, ...props }: React.HTMLAttributes<HTMLHeadingElement> & { children: React.ReactNode }) => (
                                        <h6 className="text-sm font-medium mt-3 mb-2 text-gray-900 dark:text-gray-100 uppercase tracking-wide" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </h6>
                                    ),
                                    p: ({ children, ...props }: React.HTMLAttributes<HTMLParagraphElement> & { children: React.ReactNode }) => (
                                        <p className="mt-0 mb-4 last:mb-0 leading-relaxed text-gray-800 dark:text-gray-200" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </p>
                                    ),
                                    text: ({ children }: { children: string }) => {
                                        if (typeof children === 'string') {
                                            return renderTextWithCitations(children);
                                        }
                                        return children;
                                    },
                                    code: ({ className, children, inline, ...props }: { className?: string; children: React.ReactNode; inline?: boolean }) => {
                                        const match = /language-(\w+)/.exec(className || '');
                                        const language = match ? match[1] : '';

                                        return inline ? (
                                            <code
                                                className={`${className ?? ''} ${isUser ? 'bg-gray-200 dark:bg-white/20' : 'bg-gray-800/50 dark:bg-gray-700/50'} rounded px-1.5 py-0.5 text-[0.9em] font-mono`}
                                                {...props}
                                            >
                                                {children}
                                            </code>
                                        ) : (
                                            <div className="my-4 overflow-hidden rounded-lg bg-gray-900 dark:bg-gray-950 shadow-md">
                                                <code
                                                    className={`${className ?? ''} block p-4 text-sm leading-relaxed overflow-x-auto language-${language}`}
                                                    {...props}
                                                >
                                                    {children}
                                                </code>
                                            </div>
                                        );
                                    },
                                    table: ({ children, ...props }: React.HTMLAttributes<HTMLTableElement> & { children: React.ReactNode }) => (
                                        <div className="overflow-x-auto my-3">
                                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700" {...props}>
                                                {children}
                                            </table>
                                        </div>
                                    ),
                                    td: ({ children, ...props }: React.TdHTMLAttributes<HTMLTableCellElement> & { children: React.ReactNode }) => (
                                        <td className="px-4 py-2 text-gray-800 dark:text-gray-200" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </td>
                                    ),
                                    th: ({ children, ...props }: React.ThHTMLAttributes<HTMLTableCellElement> & { children: React.ReactNode }) => (
                                        <th className="px-4 py-2 font-medium text-gray-900 dark:text-gray-100" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </th>
                                    ),
                                    a: ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { children: React.ReactNode; href?: string }) => (
                                        <a
                                            href={href}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary-500 hover:text-primary-600 dark:text-primary-400 dark:hover:text-primary-300 transition-colors"
                                            {...props}
                                        >
                                            {children}
                                        </a>
                                    ),
                                    li: ({ children, ...props }: React.LiHTMLAttributes<HTMLLIElement> & { children: React.ReactNode }) => (
                                        <li className="my-1 pl-1 marker:text-gray-500 dark:marker:text-gray-400" {...props}>
                                            <span className="block leading-relaxed">
                                                {React.Children.map(children, (child) => {
                                                    if (typeof child === 'string') {
                                                        return renderTextWithCitations(child);
                                                    }
                                                    return child;
                                                })}
                                            </span>
                                        </li>
                                    ),
                                    ul: ({ children, ...props }: React.HTMLAttributes<HTMLUListElement> & { children: React.ReactNode }) => (
                                        <ul className="list-disc pl-6 my-4 space-y-1" {...props}>
                                            {children}
                                        </ul>
                                    ),
                                    ol: ({ children, ...props }: React.HTMLAttributes<HTMLOListElement> & { children: React.ReactNode }) => (
                                        <ol className="list-decimal pl-6 my-4 space-y-1" {...props}>
                                            {children}
                                        </ol>
                                    ),
                                    blockquote: ({ children, ...props }: React.BlockquoteHTMLAttributes<HTMLQuoteElement> & { children: React.ReactNode }) => (
                                        <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-1 my-4 italic text-gray-700 dark:text-gray-300" {...props}>
                                            {React.Children.map(children, (child) => {
                                                if (typeof child === 'string') {
                                                    return renderTextWithCitations(child);
                                                }
                                                return child;
                                            })}
                                        </blockquote>
                                    ),
                                    hr: ({ ...props }: React.HTMLAttributes<HTMLHRElement>) => (
                                        <hr className="my-6 border-gray-200 dark:border-gray-700" {...props} />
                                    ),
                                    pre: ({ children, ...props }: React.HTMLAttributes<HTMLPreElement> & { children: React.ReactNode }) => (
                                        <pre className="my-4 overflow-x-auto rounded-lg bg-gray-900 dark:bg-gray-950 p-4 shadow-md" {...props}>
                                            {children}
                                        </pre>
                                    ),
                                    strong: ({ children, ...props }: React.HTMLAttributes<HTMLElement> & { children: React.ReactNode }) => (
                                        <strong className="font-semibold text-gray-900 dark:text-gray-100" {...props}>
                                            {children}
                                        </strong>
                                    ),
                                    em: ({ children, ...props }: React.HTMLAttributes<HTMLElement> & { children: React.ReactNode }) => (
                                        <em className="italic" {...props}>
                                            {children}
                                        </em>
                                    )
                                }}
                            >
                                {processMarkdown(message.content)}
                            </ReactMarkdown>

                            {/* Add CSS for citation hover effect */}
                            <style jsx global>{`
                                .citation-ref {
                                    color: #0070f3;
                                    cursor: pointer;
                                    font-weight: 600;
                                    position: relative;
                                    transition: all 0.3s ease;
                                    padding: 0 2px;
                                    border-radius: 3px;
                                    opacity: 1;
                                    will-change: opacity, background-color;
                                }
                                
                                .citation-group {
                                    display: inline;
                                    transition: opacity 0.3s ease;
                                    will-change: opacity;
                                }
                                
                                .citation-ref:hover {
                                    background-color: rgba(0, 112, 243, 0.1);
                                }
                                
                                .highlight-reference {
                                    animation: highlightFade 2s ease-out;
                                }
                                
                                @keyframes highlightFade {
                                    0%, 20% {
                                        background-color: rgba(0, 112, 243, 0.15);
                                    }
                                    100% {
                                        background-color: transparent;
                                    }
                                }
                                
                                .citation-tooltip {
                                    position: fixed;
                                    z-index: 9999;
                                    pointer-events: none;
                                    max-width: 300px;
                                    transition: all 0.2s ease;
                                    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2), 0 5px 10px -5px rgba(0,0,0,0.1);
                                    border: 1px solid rgba(226, 232, 240, 0.8);
                                    border-radius: 8px;
                                    animation: tooltipFadeIn 0.2s ease-out;
                                    backdrop-filter: blur(8px);
                                    -webkit-backdrop-filter: blur(8px);
                                    will-change: transform, opacity;
                                }
                                
                                .details-reset summary {
                                    list-style: none;
                                }
                                
                                .details-reset summary::-webkit-details-marker {
                                    display: none;
                                }
                                
                                .details-reset summary::before {
                                    content: '▼';
                                    display: inline-block;
                                    width: 20px;
                                    height: 20px;
                                    margin-left: 12px;
                                    margin-right: 16px;
                                    color: #64748b;
                                    font-size: 10px;
                                    text-align: center;
                                    transform: rotate(-90deg);
                                    transition: transform 0.2s ease;
                                }
                                
                                .details-reset[open] summary::before {
                                    transform: rotate(0deg);
                                }
                                
                                @keyframes tooltipFadeIn {
                                    from {
                                        opacity: 0;
                                        transform: translateY(5px);
                                    }
                                    to {
                                        opacity: 1;
                                        transform: translateY(0);
                                    }
                                }
                                
                                @media (prefers-color-scheme: dark) {
                                    .citation-ref {
                                        color: #60a5fa;
                                    }
                                    
                                    .citation-ref:hover {
                                        background-color: rgba(96, 165, 250, 0.1);
                                    }
                                    
                                    .citation-tooltip {
                                        border-color: rgba(17, 24, 39, 0.8);
                                        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.6), 0 5px 10px -5px rgba(0,0,0,0.5);
                                    }
                                    
                                    .details-reset summary::before {
                                        color: #94a3b8;
                                    }
                                }
                            `}</style>
                        </div>
                    </motion.div>
                </div>

                {message.references && (
                    <motion.div
                        initial={isNewMessage.current ? { opacity: 0, y: 10 } : { opacity: 1, y: 0 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={isNewMessage.current ? { delay: 0.3 } : { duration: 0 }}
                        className="mt-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 overflow-hidden"
                    >
                        <details className="overflow-hidden details-reset">
                            <summary className="font-medium text-sm pl-6 pr-4 py-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors flex items-center text-gray-700 dark:text-gray-300">
                                <div className="ml-4 flex items-center gap-3">
                                    <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                                    </svg>
                                    References
                                </div>
                            </summary>
                            <div
                                className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-800 references-content overflow-auto space-y-4"
                                style={{ maxHeight: '800px' }}
                            >
                                {(() => {
                                    try {
                                        // Try to parse as JSON
                                        const references = JSON.parse(message.references);

                                        return (
                                            <div className="references-list space-y-6">
                                                {references.map((ref: any) => (
                                                    <div
                                                        key={ref.id}
                                                        className="reference-item"
                                                        data-ref-index={ref.index}
                                                    >
                                                        <div className="flex gap-3 mb-2">
                                                            <div className="flex-shrink-0 w-6 text-gray-400">{ref.index}</div>
                                                            <div className="flex-1">
                                                                <div className="flex items-baseline gap-2 flex-wrap">
                                                                    <div className="font-medium text-gray-900 dark:text-gray-100">
                                                                        {ref.title}
                                                                    </div>
                                                                    {ref.year && (
                                                                        <div className="text-gray-500 text-xs whitespace-nowrap">
                                                                            ({ref.year})
                                                                        </div>
                                                                    )}
                                                                </div>

                                                                {ref.authors && ref.authors.length > 0 && (
                                                                    <div className="text-gray-500 text-sm mt-1">
                                                                        {ref.authors.join(', ')}
                                                                    </div>
                                                                )}

                                                                {ref.doi && (
                                                                    <div className="text-gray-500 text-sm mt-1">
                                                                        <span className="text-gray-400">DOI:</span>
                                                                        <a
                                                                            href={ref.doi.startsWith('http') ? ref.doi : `https://doi.org/${ref.doi}`}
                                                                            className="ml-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                                                            target="_blank"
                                                                            rel="noopener noreferrer"
                                                                        >
                                                                            {ref.doi}
                                                                        </a>
                                                                    </div>
                                                                )}

                                                                <div className="text-gray-500 text-sm mt-1">
                                                                    <span className="text-gray-400">ID:</span>
                                                                    <a
                                                                        href={ref.id.startsWith('http') ? ref.id : `https://${ref.id}`}
                                                                        className="ml-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                    >
                                                                        {ref.id}
                                                                    </a>
                                                                </div>

                                                                {ref.score !== null && (
                                                                    <div className="text-gray-500 text-sm mt-1">
                                                                        <span className="text-gray-400">Relevance:</span>
                                                                        <span className="ml-1">{typeof ref.score === 'number' ? ref.score.toFixed(2) : ref.score}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        );
                                    } catch (e) {
                                        // Fallback to direct HTML rendering for legacy format
                                        return (
                                            <div className="references-wrapper" dangerouslySetInnerHTML={{
                                                __html: message.references
                                            }} />
                                        );
                                    }
                                })()}
                            </div>
                        </details>
                    </motion.div>
                )}
            </div>
        </motion.div>
    );
};

const UserIcon: FC = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
    </svg>
);

const AithenaIcon: FC = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
    >
        <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
        <path d="M12 9v4" />
        <path d="M12 17h.01" />
    </svg>
);

export default MessageItem;
