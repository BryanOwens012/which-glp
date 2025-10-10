"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Check,
  X,
  TrendingDown,
  DollarSign,
  AlertCircle,
  Users,
  Info,
} from "lucide-react";
import { trpc } from "@/lib/trpc";

export const DrugComparison = () => {
  const router = useRouter();

  // Fetch real drug stats from API
  const { data: drugStats, isLoading } = trpc.drugs.getAllStats.useQuery();

  // State for selected drugs
  const [selectedMeds, setSelectedMeds] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Navigate to experiences page with drug filter
  const handleDrugClick = (drugName: string) => {
    router.push(`/experiences?drug=${encodeURIComponent(drugName)}`);
  };

  // Initialize with top 3 drugs once data is loaded
  useEffect(() => {
    if (drugStats && drugStats.length > 0 && selectedMeds.length === 0) {
      setSelectedMeds(drugStats.slice(0, 3).map((d) => d.drug));
    }
  }, [drugStats, selectedMeds.length]);

  // Prefetch experiences pages for selected drugs during idle time
  useEffect(() => {
    if (selectedMeds.length === 0) return;

    if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
      requestIdleCallback(() => {
        selectedMeds.forEach((drug) => {
          router.prefetch(`/experiences?drug=${encodeURIComponent(drug)}`);
        });
      });
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(() => {
        selectedMeds.forEach((drug) => {
          router.prefetch(`/experiences?drug=${encodeURIComponent(drug)}`);
        });
      }, 500);
    }
  }, [selectedMeds, router]);

  const toggleDrug = (drug: string) => {
    if (selectedMeds.includes(drug)) {
      if (selectedMeds.length > 1) {
        setSelectedMeds(selectedMeds.filter((m) => m !== drug));
        setErrorMessage(null);
      }
    } else {
      if (selectedMeds.length < 6) {
        setSelectedMeds([...selectedMeds, drug]);
        setErrorMessage(null);
      } else {
        setErrorMessage(
          "Maximum 6 drugs selected. Please deselect one to add another."
        );
        setTimeout(() => setErrorMessage(null), 3000);
      }
    }
  };

  const selectedDrugs =
    drugStats?.filter((med) => selectedMeds.includes(med.drug)) ?? [];

  if (isLoading) {
    return <div className="text-center py-8">Loading drugs...</div>;
  }

  if (!drugStats || drugStats.length === 0) {
    return <div className="text-center py-8">No drug data available</div>;
  }

  return (
    <div>
      {/* Drug Selector */}
      <Card className="mb-8 border-border/40 bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Select Drugs to Compare</h2>
        <div className="flex flex-wrap gap-3">
          {[...drugStats]
            .sort((a, b) => {
              if (b.count !== a.count) {
                return b.count - a.count;
              }
              return a.drug.localeCompare(b.drug);
            })
            .map((drug) => (
              <Button
                key={drug.drug}
                variant={
                  selectedMeds.includes(drug.drug) ? "default" : "outline"
                }
                onClick={() => toggleDrug(drug.drug)}
                className="gap-2"
              >
                {selectedMeds.includes(drug.drug) && (
                  <Check className="h-4 w-4" />
                )}
                {drug.drug === "GLP-1" ? "GLP-1 (General)" : drug.drug}
                <span className="ml-1 text-xs opacity-70">({drug.count})</span>
              </Button>
            ))}
        </div>
        {errorMessage && (
          <p className="mt-3 text-sm text-destructive flex items-center gap-1 animate-in fade-in-0 duration-200 animate-out fade-out-0">
            <AlertCircle className="h-4 w-4" />
            {errorMessage}
          </p>
        )}
      </Card>

      {/* Comparison Table */}
      <Tabs defaultValue="effectiveness" className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="effectiveness" className="cursor-pointer">
            Overview
          </TabsTrigger>
          <TabsTrigger value="cost" className="cursor-pointer">
            Cost & Availability
          </TabsTrigger>
          <TabsTrigger value="side-effects" className="cursor-pointer">
            Side Effects
          </TabsTrigger>
        </TabsList>

        <TabsContent value="effectiveness">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedDrugs.map((med) => (
              <Card
                key={med.drug}
                className="border-border/40 bg-card p-6 cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
                onClick={() => handleDrugClick(med.drug)}
              >
                <div className="mb-4">
                  <h3 className="text-xl font-bold">{med.drug}</h3>
                  <p className="text-sm text-muted-foreground">
                    {med.count} experiences
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <TrendingDown className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Weight Loss</span>
                    </div>
                    <div className="text-2xl font-bold text-primary flex items-center gap-2">
                      {med.avgWeightLoss ? (
                        <>
                          {med.avgWeightLoss.toFixed(1)}%
                          {med.avgDurationWeeks && (
                            <span className="text-sm text-muted-foreground font-normal">
                              (
                              {(
                                med.avgWeightLoss /
                                (med.avgDurationWeeks / 4.33)
                              ).toFixed(1)}
                              %/mo)
                            </span>
                          )}
                        </>
                      ) : (
                        <>
                          N/A
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="p-1 hover:bg-muted rounded">
                                <Info className="h-4 w-4 text-muted-foreground" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Insufficient data</TooltipContent>
                          </Tooltip>
                        </>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground flex items-center gap-1">
                      Average over{" "}
                      {med.avgDurationWeeks ? (
                        Math.round(med.avgDurationWeeks / 4.33)
                      ) : (
                        <span className="inline-flex items-center gap-1">
                          N/A
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="p-0.5 hover:bg-muted rounded inline-flex">
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Insufficient data</TooltipContent>
                          </Tooltip>
                        </span>
                      )}{" "}
                      months
                    </p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">
                      Rating
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-primary"
                          style={{
                            width: `${(med.avgSentimentPost ?? 0) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm font-semibold flex items-center gap-1">
                        {med.avgSentimentPost ? (
                          `${(med.avgSentimentPost * 10).toFixed(1)}`
                        ) : (
                          <>
                            N/A
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button className="p-0.5 hover:bg-muted rounded">
                                  <Info className="h-3 w-3 text-muted-foreground" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>Insufficient data</TooltipContent>
                            </Tooltip>
                          </>
                        )}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-medium">
                      Quality of Life
                    </div>
                    <div className="text-sm text-muted-foreground flex items-center gap-1">
                      {med.avgSentimentPre !== null &&
                      med.avgSentimentPost !== null ? (
                        <span>
                          {Math.round(med.avgSentimentPre * 100)}% →{" "}
                          {Math.round(med.avgSentimentPost * 100)}%
                        </span>
                      ) : (
                        <>
                          N/A
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button className="p-0.5 hover:bg-muted rounded">
                                <Info className="h-3 w-3 text-muted-foreground" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent>Insufficient data</TooltipContent>
                          </Tooltip>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="side-effects">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedDrugs.map((med) => (
              <Card
                key={med.drug}
                className="border-border/40 bg-card p-6 cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
                onClick={() => handleDrugClick(med.drug)}
              >
                <h3 className="mb-4 text-xl font-bold">{med.drug}</h3>

                {med.commonSideEffects.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mb-3" />
                    <p className="text-sm text-muted-foreground">
                      Insufficient data
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 text-sm font-medium">
                        Most Common Side Effects
                      </div>
                      <ul className="space-y-1">
                        {med.commonSideEffects.slice(0, 5).map((effect) => {
                          // Parse JSON string to extract the actual name
                          let effectName = effect.name;
                          try {
                            const parsed = JSON.parse(effect.name);
                            effectName = parsed.name;
                          } catch {
                            // Keep original if parsing fails
                          }
                          return (
                            <li
                              key={effect.name}
                              className="flex items-start gap-2 text-sm"
                            >
                              <X className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                              <div className="flex-1">
                                <span className="text-muted-foreground capitalize">
                                  {effectName}
                                </span>
                                <span className="ml-2 text-xs">
                                  ({Math.round(effect.percentage)}%)
                                </span>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>

                    <div className="pt-4 border-t border-border/40">
                      <div className="text-sm font-medium mb-2">
                        Severity Distribution{" "}
                        <span className="text-xs font-normal text-muted-foreground">
                          (among the {Math.round(med.sideEffectReportingRate)}%
                          who reported side effects)
                        </span>
                      </div>
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-rose-900"></span>
                            <span className="text-muted-foreground">
                              Severe
                            </span>
                          </span>
                          <span className="font-semibold">
                            {Math.round(med.sideEffectSeverity.severe)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-red-500"></span>
                            <span className="text-muted-foreground">
                              Moderate
                            </span>
                          </span>
                          <span className="font-semibold">
                            {Math.round(med.sideEffectSeverity.moderate)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                            <span className="text-muted-foreground">Mild</span>
                          </span>
                          <span className="font-semibold">
                            {Math.round(med.sideEffectSeverity.mild)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="cost">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedDrugs.map((med) => {
              const totalSources =
                med.drugSources.brand +
                med.drugSources.compounded +
                med.drugSources.outOfPocket +
                med.drugSources.other;
              const hasData = med.avgCostPerMonth !== null || totalSources > 0;

              return (
                <Card
                  key={med.drug}
                  className="border-border/40 bg-card p-6 cursor-pointer transition-all hover:shadow-lg hover:border-primary/50"
                  onClick={() => handleDrugClick(med.drug)}
                >
                  <h3 className="mb-4 text-xl font-bold">{med.drug}</h3>

                  {!hasData ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <DollarSign className="h-12 w-12 text-muted-foreground mb-3" />
                      <p className="text-sm text-muted-foreground">
                        Insufficient data
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <div className="mb-2 flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-primary" />
                          <span className="text-sm font-medium">
                            Monthly Cost
                          </span>
                        </div>
                        <div className="text-2xl font-bold flex items-center gap-2">
                          {med.avgCostPerMonth ? (
                            `$${Math.round(med.avgCostPerMonth)}`
                          ) : (
                            <>
                              $N/A
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <button className="p-1 hover:bg-muted rounded">
                                    <Info className="h-4 w-4 text-muted-foreground" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent>
                                  Insufficient data
                                </TooltipContent>
                              </Tooltip>
                            </>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="mb-2 text-sm text-muted-foreground">
                          Insurance Coverage
                        </div>
                        <div className="text-2xl font-bold text-primary">
                          {(() => {
                            const coverage =
                              totalSources > 0
                                ? Math.round(
                                    (med.drugSources.brand / totalSources) * 100
                                  )
                                : 0;
                            return coverage;
                          })()}
                          %
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          using brand name (likely insured)
                        </p>
                      </div>

                      <div className="pt-4 border-t border-border/40">
                        <div className="text-sm font-medium mb-2">
                          Drug Sources
                        </div>
                        <div className="space-y-1 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">Brand</span>
                            <span className="font-semibold">
                              {totalSources > 0
                                ? `${Math.round(
                                    (med.drugSources.brand / totalSources) * 100
                                  )}%`
                                : "0%"}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">
                              Compounded
                            </span>
                            <span className="font-semibold">
                              {totalSources > 0
                                ? `${Math.round(
                                    (med.drugSources.compounded /
                                      totalSources) *
                                      100
                                  )}%`
                                : "0%"}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground">
                              Out-of-Pocket
                            </span>
                            <span className="font-semibold">
                              {totalSources > 0
                                ? `${Math.round(
                                    (med.drugSources.outOfPocket /
                                      totalSources) *
                                      100
                                  )}%`
                                : "0%"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
