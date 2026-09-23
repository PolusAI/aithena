'use client';

import React, { useState } from "react";
import { StatsDashboard } from "@/components/StatsDashboard";
import { SearchInterface } from "@/components/SearchInterface";
import ThemeToggle from "@/components/ThemeToggle";
import TrialGPTChat from "@/components/TrialGPTChat";

type Tab = "search" | "match";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("search");

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      {/* Top Navigation Bar */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-card)]/50 glass-effect sticky top-0 z-50">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          {/* Left: Logo + Nav Tabs */}
          <div className="flex items-center gap-6">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/gardian/GARD_Logo.svg"
              alt="GARD Logo"
              className="h-8 w-auto"
            />

            <nav className="flex gap-1" aria-label="Tabs">
              <button
                onClick={() => setActiveTab("search")}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-md transition-colors
                  ${activeTab === "search"
                    ? "bg-[#1b568b]/10 text-[#1b568b] dark:bg-[#00d4ff]/10 dark:text-[#00d4ff]"
                    : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-gray-100 dark:hover:bg-gray-800"
                  }
                `}
              >
                Search Trials
              </button>
              <button
                onClick={() => setActiveTab("match")}
                className={`
                  px-3 py-1.5 text-sm font-medium rounded-md transition-colors
                  ${activeTab === "match"
                    ? "bg-[#1b568b]/10 text-[#1b568b] dark:bg-[#00d4ff]/10 dark:text-[#00d4ff]"
                    : "text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-gray-100 dark:hover:bg-gray-800"
                  }
                `}
              >
                Match Patient
              </button>
            </nav>
          </div>

          {/* Right: Theme Toggle */}
          <ThemeToggle />
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {/* Search Trials Tab */}
        {activeTab === "search" && (
          <section className="space-y-6">
            {/* Hero + Stats */}
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                <span className="text-[#7f2754]">GARD</span>
                <span className="text-[#1b568b] dark:text-[#00d4ff]">IAN</span>
              </h1>
              <p className="text-sm text-[var(--color-muted-foreground)] mt-1">
                Linking individuals with rare diseases to clinical trials
              </p>
            </div>
            <StatsDashboard />
            <SearchInterface />
          </section>
        )}

        {/* Match Patient Tab */}
        {activeTab === "match" && (
          <section>
            <TrialGPTChat />
          </section>
        )}
      </main>
    </div>
  );
}
