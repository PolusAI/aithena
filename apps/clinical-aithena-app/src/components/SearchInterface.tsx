"use client";

import React, { useState, useEffect } from "react";
import { Input } from "./Input";
import { Button } from "./Button";
import { StudyCard } from "./StudyCard";
import { api } from "../services/api";
import { CTGovStudy, Status, StudiesParams } from "../types/models";

export const SearchInterface = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "recruiting">("all");
  const [studies, setStudies] = useState<CTGovStudy[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStudies = async () => {
      setLoading(true);
      setError("");
      try {
        const params: StudiesParams = {
          term: searchQuery,
          pageSize: 20,
        };

        if (activeTab === "recruiting") {
          params["filter.overallStatus"] = [Status.RECRUITING];
        }

        const response = await api.searchStudies(params);
        setStudies(response.studies);
      } catch (err) {
        console.error(err);
        setError("Failed to load studies. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    // Debounce search
    const timeoutId = setTimeout(() => {
      fetchStudies();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, activeTab]);

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:max-w-xl">
          <Input
            placeholder="Search studies by condition, drug, or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={
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
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.3-4.3" />
              </svg>
            }
            className="w-full"
          />
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
           <Button variant="outline" className="w-full sm:w-auto">
             Filters
             <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="ml-2"
              >
                <line x1="4" x2="4" y1="21" y2="14" />
                <line x1="4" x2="4" y1="10" y2="3" />
                <line x1="12" x2="12" y1="21" y2="12" />
                <line x1="12" x2="12" y1="8" y2="3" />
                <line x1="20" x2="20" y1="21" y2="16" />
                <line x1="20" x2="20" y1="12" y2="3" />
                <line x1="1" x2="7" y1="14" y2="14" />
                <line x1="9" x2="15" y1="8" y2="8" />
                <line x1="17" x2="23" y1="16" y2="16" />
              </svg>
           </Button>
           <Button className="w-full sm:w-auto">Search</Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-[var(--color-border)] pb-1">
        <button
          className={`pb-3 px-1 text-sm font-medium transition-colors ${
            activeTab === "all"
              ? "border-b-2 border-[var(--color-primary)] text-[var(--color-primary)]"
              : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
          }`}
          onClick={() => setActiveTab("all")}
        >
          All Studies
        </button>
        <button
          className={`pb-3 px-1 text-sm font-medium transition-colors ${
            activeTab === "recruiting"
              ? "border-b-2 border-[var(--color-primary)] text-[var(--color-primary)]"
              : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)]"
          }`}
          onClick={() => setActiveTab("recruiting")}
        >
          Recruiting
        </button>
      </div>

      {/* Results List */}
      <div className="grid gap-4">
        {loading ? (
             <div className="text-center py-12 text-[var(--color-muted-foreground)]">
                Loading studies...
             </div>
        ) : error ? (
             <div className="text-center py-12 text-red-500">
                {error}
             </div>
        ) : studies.length > 0 ? (
          studies.map((study) => (
            <StudyCard key={study.id} study={study} />
          ))
        ) : (
          <div className="text-center py-12 text-[var(--color-muted-foreground)]">
            No studies found matching your criteria.
          </div>
        )}
      </div>
    </div>
  );
};
