'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { TrialMatch } from '@/types/trialgpt';

interface TrialResultCardProps {
    trial: TrialMatch;
}

/** Max characters to show before truncating with "read more" */
const TRUNCATE_LEN = 180;

function TruncatedText({ text, label }: { text: string; label: string }) {
    const [expanded, setExpanded] = useState(false);
    const needsTruncation = text.length > TRUNCATE_LEN;

    return (
        <div>
            <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-0.5">
                {label}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
                {!needsTruncation || expanded
                    ? text
                    : `${text.slice(0, TRUNCATE_LEN).trimEnd()}...`}
                {needsTruncation && (
                    <button
                        type="button"
                        onClick={() => setExpanded(!expanded)}
                        className="ml-1 text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium"
                    >
                        {expanded ? 'show less' : 'read more'}
                    </button>
                )}
            </p>
        </div>
    );
}

const TrialResultCard: React.FC<TrialResultCardProps> = ({ trial }) => {
    const getRelevanceColor = (score: number) => {
        if (score >= 80) return 'text-green-600 dark:text-green-400';
        if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
        return 'text-gray-600 dark:text-gray-400';
    };

    const getEligibilityLabel = (score: number) => {
        if (score > 0) return { text: 'Likely Eligible', color: 'text-green-600 dark:text-green-400' };
        if (score === 0) return { text: 'Uncertain', color: 'text-gray-600 dark:text-gray-400' };
        return { text: 'May Not Qualify', color: 'text-orange-600 dark:text-orange-400' };
    };

    const eligibilityLabel = getEligibilityLabel(trial.eligibility_score);

    return (
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow bg-white dark:bg-gray-800">
            {/* Header row: rank + NCT ID + scores */}
            <div className="flex items-start justify-between gap-4 mb-2">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                            #{trial.rank}
                        </span>
                        <Link
                            href={`/study/${trial.nct_id}`}
                            className="text-xs font-mono text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                        >
                            {trial.nct_id}
                        </Link>
                    </div>
                    <Link
                        href={`/study/${trial.nct_id}`}
                        className="font-semibold text-sm text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 line-clamp-2"
                    >
                        {trial.title}
                    </Link>
                </div>

                {/* Compact scores */}
                <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                        <div className={`text-lg font-bold leading-tight ${getRelevanceColor(trial.relevance_score)}`}>
                            {trial.relevance_score.toFixed(0)}
                        </div>
                        <div className="text-[10px] text-gray-500 dark:text-gray-400">relevance</div>
                    </div>
                    <div className="text-right">
                        <div className={`text-sm font-semibold leading-tight ${eligibilityLabel.color}`}>
                            {eligibilityLabel.text}
                        </div>
                        <div className="text-[10px] text-gray-500 dark:text-gray-400">
                            score: {trial.eligibility_score.toFixed(1)}
                        </div>
                    </div>
                </div>
            </div>

            {/* Truncated explanations */}
            <div className="space-y-2 pt-2 border-t border-gray-100 dark:border-gray-700">
                <TruncatedText text={trial.relevance_explanation} label="Why this trial matches:" />
                <TruncatedText text={trial.eligibility_explanation} label="Eligibility assessment:" />
            </div>
        </div>
    );
};

export default TrialResultCard;
