"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DrugStatCard } from "@/components/drug-stat-card"
import { Check } from "lucide-react"
import { trpc } from "@/lib/trpc"

// Helper to format drug names for display
const formatDrugName = (drug: string) => drug === "GLP-1" ? "GLP-1 (General)" : drug

const ComparePage = () => {
  const [selectedDrugs, setSelectedDrugs] = useState<string[]>(["Wegovy", "Mounjaro", "Ozempic"])

  // Fetch all drug stats from backend
  const { data: allDrugs, isLoading } = trpc.drugs.getAllStats.useQuery()

  const toggleDrug = (drug: string) => {
    if (selectedDrugs.includes(drug)) {
      if (selectedDrugs.length > 1) {
        setSelectedDrugs(selectedDrugs.filter((d) => d !== drug))
      }
    } else {
      if (selectedDrugs.length < 4) {
        setSelectedDrugs([...selectedDrugs, drug])
      }
    }
  }

  const selectedDrugStats = allDrugs?.filter((drug) => selectedDrugs.includes(drug.drug)) ?? []

  if (isLoading) {
    return (
      <div className="min-h-screen">
        <Navigation />
        <div className="container mx-auto px-4 pt-24 pb-12">
          <div className="text-center">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Navigation />

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="mb-3 text-4xl font-bold">Compare GLP-1 Medications</h1>
          <p className="text-lg text-muted-foreground">
            Select up to 4 medications to compare based on real user experiences from Reddit
          </p>
        </div>

        {/* Drug Selector */}
        <Card className="mb-8 border-border/40 bg-card p-6">
          <h2 className="mb-4 text-lg font-semibold">Select Medications to Compare</h2>
          <div className="flex flex-wrap gap-3">
            {allDrugs?.map((drug) => (
              <Button
                key={drug.drug}
                variant={selectedDrugs.includes(drug.drug) ? "default" : "outline"}
                onClick={() => toggleDrug(drug.drug)}
                className="gap-2"
              >
                {selectedDrugs.includes(drug.drug) && <Check className="h-4 w-4" />}
                {formatDrugName(drug.drug)}
                <span className="ml-1 text-xs opacity-70">({drug.count})</span>
              </Button>
            ))}
          </div>
          <p className="mt-3 text-sm text-muted-foreground">
            {selectedDrugs.length}/4 medications selected
            {allDrugs && ` • Data from ${allDrugs.reduce((sum, d) => sum + d.count, 0).toLocaleString()} user experiences`}
          </p>
        </Card>

        {/* Comparison Tabs */}
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
            <TabsTrigger value="side-effects">Side Effects</TabsTrigger>
            <TabsTrigger value="cost">Cost & Access</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {selectedDrugStats.map((stats) => (
                <DrugStatCard key={stats.drug} stats={stats} />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="effectiveness" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {selectedDrugStats.map((stats) => (
                <Card key={stats.drug} className="border-border/40 bg-card p-6">
                  <h3 className="mb-4 text-xl font-bold">{formatDrugName(stats.drug)}</h3>

                  <div className="space-y-4">
                    {/* Weight Loss */}
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Average Weight Loss</div>
                      <div className="text-3xl font-bold text-primary">
                        {stats.avgWeightLoss?.toFixed(1) || "N/A"}%
                      </div>
                      {stats.avgWeightLossLbs && (
                        <p className="text-xs text-muted-foreground mt-1">
                          ~{Math.round(stats.avgWeightLossLbs)} lbs
                        </p>
                      )}
                    </div>

                    {/* Duration */}
                    {stats.avgDurationWeeks && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Average Duration</div>
                        <div className="text-lg font-semibold">
                          {Math.round(stats.avgDurationWeeks / 4.33)} months
                        </div>
                      </div>
                    )}

                    {/* Sentiment Change */}
                    {stats.avgSentimentPre !== null && stats.avgSentimentPost !== null && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Quality of Life</div>
                        <div className="flex items-center gap-2 text-sm">
                          <span>{Math.round(stats.avgSentimentPre * 100)}%</span>
                          <span className="text-muted-foreground">→</span>
                          <span className="text-primary font-semibold">
                            {Math.round(stats.avgSentimentPost * 100)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Recommendation */}
                    {stats.avgRecommendationScore !== null && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Avg Rating</div>
                        <div className="text-2xl font-bold text-primary">
                          {(stats.avgRecommendationScore * 10).toFixed(1)}/10
                        </div>
                      </div>
                    )}

                    {/* Plateau & Rebound */}
                    <div className="pt-4 border-t border-border/40">
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div>
                          <div className="text-muted-foreground">Plateau Rate</div>
                          <div className="font-semibold">{Math.round(stats.plateauRate)}%</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Rebound Rate</div>
                          <div className="font-semibold">{Math.round(stats.reboundRate)}%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="side-effects" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {selectedDrugStats.map((stats) => (
                <Card key={stats.drug} className="border-border/40 bg-card p-6">
                  <h3 className="mb-4 text-xl font-bold">{formatDrugName(stats.drug)}</h3>

                  <div className="space-y-4">
                    {/* Common Side Effects */}
                    <div>
                      <div className="text-sm font-medium mb-3">Most Common Side Effects</div>
                      <div className="space-y-2">
                        {stats.commonSideEffects.slice(0, 5).map((effect) => (
                          <div key={effect.name} className="flex items-center justify-between">
                            <span className="text-sm capitalize text-muted-foreground">
                              {effect.name}
                            </span>
                            <div className="flex items-center gap-2">
                              <div className="h-2 w-24 bg-muted rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-destructive"
                                  style={{ width: `${effect.percentage}%` }}
                                />
                              </div>
                              <span className="text-sm font-semibold w-12 text-right">
                                {Math.round(effect.percentage)}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Severity Breakdown */}
                    <div className="pt-4 border-t border-border/40">
                      <div className="text-sm font-medium mb-2">Severity Distribution</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Mild</span>
                          <span className="font-semibold">{Math.round(stats.sideEffectSeverity.mild)}%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Moderate</span>
                          <span className="font-semibold">{Math.round(stats.sideEffectSeverity.moderate)}%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Severe</span>
                          <span className="font-semibold text-destructive">
                            {Math.round(stats.sideEffectSeverity.severe)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Sample Size */}
                    <div className="pt-4 border-t border-border/40 text-xs text-muted-foreground">
                      Based on {stats.count.toLocaleString()} user reports
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="cost" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {selectedDrugStats.map((stats) => (
                <Card key={stats.drug} className="border-border/40 bg-card p-6">
                  <h3 className="mb-4 text-xl font-bold">{formatDrugName(stats.drug)}</h3>

                  <div className="space-y-4">
                    {/* Average Cost */}
                    {stats.avgCostPerMonth && (
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Average Monthly Cost</div>
                        <div className="text-3xl font-bold">${Math.round(stats.avgCostPerMonth)}</div>
                        <p className="text-xs text-muted-foreground mt-1">Without insurance</p>
                      </div>
                    )}

                    {/* Insurance Coverage */}
                    <div>
                      <div className="text-sm text-muted-foreground mb-1">Insurance Coverage</div>
                      <div className="text-2xl font-bold text-primary">
                        {Math.round(stats.insuranceCoverage)}%
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">of users have coverage</p>
                    </div>

                    {/* Drug Sources */}
                    <div className="pt-4 border-t border-border/40">
                      <div className="text-sm font-medium mb-2">Drug Sources</div>
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Brand</span>
                          <span className="font-semibold">{stats.drugSources.brand}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Compounded</span>
                          <span className="font-semibold">{stats.drugSources.compounded}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Out-of-Pocket</span>
                          <span className="font-semibold">{stats.drugSources.outOfPocket}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Other</span>
                          <span className="font-semibold">{stats.drugSources.other}</span>
                        </div>
                      </div>
                    </div>

                    {/* Access Issues */}
                    <div className="pt-4 border-t border-border/40">
                      <div className="text-sm text-muted-foreground mb-1">Pharmacy Access Issues</div>
                      <div className="text-lg font-semibold">
                        {Math.round(stats.pharmacyAccessIssues)}%
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        reported difficulty finding medication
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* Bottom CTA */}
        <Card className="mt-8 border-border/40 bg-card/50 p-8 text-center">
          <h2 className="mb-3 text-2xl font-bold">Need personalized recommendations?</h2>
          <p className="mb-6 text-muted-foreground">
            Get predictions based on your specific profile, location, and health conditions
          </p>
          <Button size="lg" asChild>
            <a href="/predict">Get Personalized Prediction</a>
          </Button>
        </Card>
      </div>
    </div>
  )
}

export default ComparePage
