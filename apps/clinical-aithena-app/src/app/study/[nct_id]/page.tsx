import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { api } from "@/services/api";
import { Badge } from "@/components/Badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/Card";
import { Status } from "@/types/models";
import ThemeToggle from "@/components/ThemeToggle";
import Image from "next/image";

export default async function StudyPage({
  params,
}: {
  params: Promise<{ nct_id: string }>;
}) {
  const { nct_id } = await params;
  const study = await api.getStudy(nct_id);

  if (!study) {
    notFound();
  }

  const ps = study.protocolSection;
  const idModule = ps?.identificationModule;
  const statusModule = ps?.statusModule;
  const designModule = ps?.designModule;
  const eligibility = ps?.eligibilityModule;
  const contacts = ps?.contactsLocationsModule;

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

  return (
    <div className="min-h-screen bg-[var(--color-background)] pb-12">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-card)]/50 glass-effect sticky top-0 z-50">
        <div className="container mx-auto px-4 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-3 mr-4">
                <div className="relative h-8 w-[407px]">
                   <Image 
                     src="/GARD_Logo.svg" 
                     alt="GARD Logo" 
                     fill
                     className="object-contain"
                   />
                </div>
                <div className="flex flex-col">
                  <span className="text-lg font-bold">
                    <span className="text-[#7f2754]">GARD</span>
                    <span className="text-[#1b568b] dark:text-[#00d4ff]">IAN</span>
                  </span>
                  <span className="text-xs">
                    <span className="text-[#7f2754]">GARD</span>
                    <span className="text-[#1b568b] dark:text-[#00d4ff]"> Intelligent Association Network</span>
                  </span>
                </div>
            </Link>
            <Link
              href="/"
              className="text-sm font-medium text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] flex items-center gap-1 transition-colors"
            >
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
              >
                <path d="m15 18-6-6 6-6" />
              </svg>
              Back to Search
            </Link>
          </div>
           <div className="flex items-center gap-4">
            <span className="text-sm font-mono text-[var(--color-muted-foreground)] bg-[var(--color-muted)] px-2 py-1 rounded">
                {study.nct_id}
            </span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-5xl space-y-8">
        {/* Title Section */}
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--color-foreground)]">
              {idModule?.briefTitle}
            </h1>
            <Badge variant={getStatusVariant(study.overall_status)} className="text-sm px-3 py-1">
              {study.overall_status?.replace(/_/g, " ")}
            </Badge>
          </div>
          <p className="text-lg text-[var(--color-muted-foreground)]">
            {idModule?.officialTitle}
          </p>
          <div className="flex flex-wrap gap-4 text-sm">
             {idModule?.organization?.fullName && (
                 <div className="flex items-center gap-2">
                     <span className="font-semibold text-[var(--color-foreground)]">Sponsor:</span>
                     <span className="text-[var(--color-muted-foreground)]">{idModule.organization.fullName}</span>
                 </div>
             )}
             {designModule?.studyType && (
                 <div className="flex items-center gap-2">
                     <span className="font-semibold text-[var(--color-foreground)]">Type:</span>
                     <span className="text-[var(--color-muted-foreground)]">{designModule.studyType}</span>
                 </div>
             )}
             {designModule?.phases && (
                 <div className="flex items-center gap-2">
                     <span className="font-semibold text-[var(--color-foreground)]">Phase:</span>
                     <span className="text-[var(--color-muted-foreground)]">{designModule.phases.join(", ")}</span>
                 </div>
             )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="md:col-span-2 space-y-8">
            {/* Description */}
            <Card>
                <CardHeader>
                    <CardTitle>Description</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed whitespace-pre-line">
                        {ps?.descriptionModule?.detailedDescription || ps?.descriptionModule?.briefSummary || "No description available."}
                    </div>
                </CardContent>
            </Card>

             {/* Eligibility */}
            <Card>
                <CardHeader>
                    <CardTitle>Eligibility</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                        <div>
                            <span className="font-semibold block text-[var(--color-muted-foreground)]">Gender</span>
                            <span>{eligibility?.sex}</span>
                        </div>
                        <div>
                            <span className="font-semibold block text-[var(--color-muted-foreground)]">Age Limits</span>
                            <span>{eligibility?.minimumAge || "N/A"} to {eligibility?.maximumAge || "N/A"}</span>
                        </div>
                         <div>
                            <span className="font-semibold block text-[var(--color-muted-foreground)]">Healthy Volunteers</span>
                            <span>{eligibility?.healthyVolunteers ? "Accepts Healthy Volunteers" : "No Healthy Volunteers"}</span>
                        </div>
                    </div>
                    <div className="border-t border-[var(--color-border)] pt-4">
                         <h4 className="font-semibold mb-2">Criteria</h4>
                         <div className="prose dark:prose-invert max-w-none text-sm whitespace-pre-line bg-[var(--color-muted)]/50 p-4 rounded-md">
                             {eligibility?.eligibilityCriteria}
                         </div>
                    </div>
                </CardContent>
            </Card>
            
             {/* Interventions/Arms */}
             {ps?.armsInterventionsModule && (
                <Card>
                    <CardHeader>
                        <CardTitle>Arms & Interventions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-6">
                            {ps.armsInterventionsModule.armGroups?.map((arm, idx) => (
                                <div key={idx} className="border-b border-[var(--color-border)] last:border-0 pb-4 last:pb-0">
                                    <div className="flex items-center justify-between mb-2">
                                        <h4 className="font-semibold">{arm.label}</h4>
                                        <Badge variant="outline">{arm.type}</Badge>
                                    </div>
                                    <p className="text-sm text-[var(--color-muted-foreground)] mb-2">{arm.description}</p>
                                    {arm.interventionNames && (
                                        <div className="text-sm">
                                            <span className="font-medium">Interventions: </span>
                                            {arm.interventionNames.join(", ")}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
             )}
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
             {/* Dates */}
             <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Key Dates</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                     <div className="flex justify-between">
                        <span className="text-[var(--color-muted-foreground)]">Start Date</span>
                        <span className="font-medium text-right">{statusModule?.startDateStruct?.date} ({statusModule?.startDateStruct?.type})</span>
                     </div>
                      <div className="flex justify-between">
                        <span className="text-[var(--color-muted-foreground)]">Completion</span>
                        <span className="font-medium text-right">{statusModule?.completionDateStruct?.date} ({statusModule?.completionDateStruct?.type})</span>
                     </div>
                      <div className="flex justify-between">
                        <span className="text-[var(--color-muted-foreground)]">Last Update</span>
                        <span className="font-medium text-right">{statusModule?.lastUpdateSubmitDate}</span>
                     </div>
                </CardContent>
             </Card>

             {/* Locations/Contacts */}
             <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Contacts & Locations</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6 text-sm">
                    {contacts?.centralContacts && contacts.centralContacts.length > 0 && (
                        <div>
                            <h4 className="font-semibold mb-2 text-[var(--color-muted-foreground)]">Central Contacts</h4>
                            <ul className="space-y-3">
                                {contacts.centralContacts.map((contact, idx) => (
                                    <li key={idx}>
                                        <div className="font-medium">{contact.name}</div>
                                        {contact.email && <div className="text-[var(--color-primary)]">{contact.email}</div>}
                                        {contact.phone && <div className="text-[var(--color-muted-foreground)]">{contact.phone}</div>}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                     <div>
                        <div className="flex items-center justify-between mb-2">
                             <h4 className="font-semibold text-[var(--color-muted-foreground)]">Locations</h4>
                             <Badge variant="outline">{contacts?.locations?.length || 0}</Badge>
                        </div>
                        <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                            {contacts?.locations?.slice(0, 10).map((loc, idx) => (
                                <div key={idx} className="border-b border-[var(--color-border)] last:border-0 pb-2 last:pb-0">
                                    <div className="font-medium">{loc.facility}</div>
                                    <div className="text-[var(--color-muted-foreground)] text-xs">
                                        {loc.city}, {loc.state}, {loc.country}
                                    </div>
                                    <div className="text-xs mt-1">
                                        <span className={`inline-block w-2 h-2 rounded-full mr-1 ${
                                            loc.status === Status.RECRUITING ? "bg-green-500" : "bg-gray-300"
                                        }`}></span>
                                        {loc.status}
                                    </div>
                                </div>
                            ))}
                             {contacts?.locations && contacts.locations.length > 10 && (
                                <div className="text-xs text-[var(--color-muted-foreground)] text-center pt-2">
                                    And {contacts.locations.length - 10} more...
                                </div>
                            )}
                        </div>
                    </div>
                </CardContent>
             </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
