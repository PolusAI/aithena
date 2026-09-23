// GARDIAN patient-trial matching types

export interface MatchRequest {
    clinical_note: string;
    demographics?: Record<string, string | number>;
    top_n?: number;
    retrieval_method?: 'bm25' | 'vector' | 'hybrid';
    session_id?: string;
}

export interface KeywordsGenerated {
    summary: string;
    conditions: string[];
}

export interface TrialMatch {
    nct_id: string;
    title: string;
    relevance_score: number;
    eligibility_score: number;
    relevance_explanation: string;
    eligibility_explanation: string;
    rank: number;
}

export interface TrialMatchResponse {
    results: TrialMatch[];
    total_retrieved: number;
    keywords_generated?: KeywordsGenerated | null;
    execution_time_ms: number;
}

export interface StatusUpdate {
    status: string;
    message: string;
    timestamp: Date;
}
