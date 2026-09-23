import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "./Card";
import { Badge } from "./Badge";
import { CTGovStudy, Status } from "../types/models";

interface StudyCardProps {
  study: CTGovStudy;
}

export const StudyCard = ({ study }: StudyCardProps) => {
  const getStatusVariant = (status?: string) => {
    switch (status) {
      case Status.RECRUITING:
      case Status.AVAILABLE:
      case Status.APPROVED_FOR_MARKETING:
        return "success";
      case Status.ACTIVE_NOT_RECRUITING:
      case Status.ENROLLING_BY_INVITATION:
        return "default";
      case Status.WITHDRAWN:
      case Status.TERMINATED:
      case Status.SUSPENDED:
        return "destructive";
      default:
        return "outline";
    }
  };

  const conditions =
    study.protocolSection?.conditionsModule?.conditions?.slice(0, 3) || [];
  const locationCount =
    study.protocolSection?.contactsLocationsModule?.locations?.length || 0;
  const phases = study.protocolSection?.designModule?.phases?.join(", ") || "N/A";
  
  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start gap-4">
          <div className="space-y-1">
            <Link
              href={`/study/${study.nct_id}`}
              className="hover:underline text-[var(--color-primary)]"
            >
              <CardTitle className="text-xl text-[var(--color-foreground)] group-hover:text-[var(--color-primary)]">
                {study.brief_title || study.protocolSection?.identificationModule?.briefTitle}
              </CardTitle>
            </Link>
            <p className="text-sm text-[var(--color-muted-foreground)]">
              {study.nct_id} • {study.study_type} • {phases}
            </p>
          </div>
          <Badge variant={getStatusVariant(study.overall_status)}>
            {study.overall_status?.replace(/_/g, " ")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm line-clamp-2 mb-4 text-[var(--color-foreground)]">
          {study.protocolSection?.descriptionModule?.briefSummary}
        </p>
        <div className="flex flex-wrap gap-2 mb-2">
          {conditions.map((condition) => (
            <Badge key={condition} variant="outline" className="font-normal text-[var(--color-muted-foreground)]">
              {condition}
            </Badge>
          ))}
          {(study.protocolSection?.conditionsModule?.conditions?.length || 0) > 3 && (
            <span className="text-xs text-[var(--color-muted-foreground)] self-center">
              +{ (study.protocolSection?.conditionsModule?.conditions?.length || 0) - 3 } more
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs text-[var(--color-muted-foreground)] mt-4">
          <div className="flex items-center gap-1">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <span>{study.enrollment_count || study.protocolSection?.designModule?.enrollmentInfo?.count || "N/A"} Enrolled</span>
          </div>
          <div className="flex items-center gap-1">
             <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            <span>{locationCount} Locations</span>
          </div>
          <div className="flex items-center gap-1 ml-auto">
            <span>Updated: {study.protocolSection?.statusModule?.lastUpdateSubmitDate || "N/A"}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

