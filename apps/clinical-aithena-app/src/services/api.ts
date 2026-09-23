import { CTGovStudy, StudiesParams, StudiesResponse } from "../types/models";
import { TrialMatchResponse } from "../types/trialgpt";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_BASE_URL) {
  console.warn(
    "⚠️  NEXT_PUBLIC_API_URL is not set. Please create a .env file with your API URL.\n" +
    "   See env.example for reference."
  );
}

export const api = {
  async searchStudies(params: StudiesParams): Promise<StudiesResponse> {
    if (!API_BASE_URL) {
      throw new Error(
        "API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL in your .env file."
      );
    }

    const queryParams = new URLSearchParams();
    
    // Map frontend params to backend /search endpoint params
    if (params.term || params["query.term"]) {
      queryParams.append("keyword", params.term || params["query.term"] || "");
    }
    
    // Map page size
    if (params.pageSize) {
      queryParams.append("page_size", String(params.pageSize));
    }
    
    // Map page (backend uses 1-indexed pages)
    if (params.pageToken) {
      // If pageToken is numeric, use it as page number
      const pageNum = parseInt(params.pageToken);
      if (!isNaN(pageNum)) {
        queryParams.append("page", String(pageNum));
      }
    } else {
      queryParams.append("page", "1");
    }

    const res = await fetch(`${API_BASE_URL}/search?${queryParams.toString()}`);
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Failed to fetch studies: ${res.status} ${errorText}`);
    }
    
    const data = await res.json();
    
    // Map backend response to frontend format
    return {
      studies: data.results as CTGovStudy[],
      totalCount: data.total,
      nextPageToken: data.page < data.total_pages ? String(data.page + 1) : undefined,
    };
  },

  async getStudy(nctId: string): Promise<CTGovStudy | null> {
    if (!API_BASE_URL) {
      throw new Error(
        "API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL in your .env file."
      );
    }

    // Search for the specific NCT ID
    const res = await fetch(`${API_BASE_URL}/search?keyword=${nctId}&page_size=1`);
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Failed to fetch study: ${res.status} ${errorText}`);
    }
    
    const data = await res.json();
    
    // Find exact match
    const study = data.results.find((s: CTGovStudy) => s.nct_id === nctId);
    return study || null;
  },

  async getStats(): Promise<{ 
    total: number; 
    recruiting: number; 
    interventional: number;
    observational: number;
  }> {
    if (!API_BASE_URL) {
      throw new Error(
        "API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL in your .env file."
      );
    }

    const res = await fetch(`${API_BASE_URL}/stats`);
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Failed to fetch stats: ${res.status} ${errorText}`);
    }
    return res.json();
  },

  async matchPatient(params: {
    clinical_note: string;
    demographics?: Record<string, string | number>;
    top_n?: number;
    retrieval_method?: "hybrid" | "bm25" | "vector";
    session_id?: string;
  }): Promise<TrialMatchResponse> {
    if (!API_BASE_URL) {
      throw new Error(
        "API_BASE_URL is not configured. Please set NEXT_PUBLIC_API_URL in your .env file."
      );
    }

    const res = await fetch(`${API_BASE_URL}/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Failed to match patient: ${res.status} ${errorText}`);
    }

    return res.json();
  },
};

