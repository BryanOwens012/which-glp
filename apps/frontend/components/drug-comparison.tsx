"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Check, X, TrendingUp, DollarSign, AlertCircle, Users } from "lucide-react"
import { trpc } from "@/lib/trpc"

export const DrugComparison = () => {
  // Fetch real drug stats from API
  const { data: drugStats, isLoading } = trpc.drugs.getAllStats.useQuery()

  // State for selected medications
  const [selectedMeds, setSelectedMeds] = useState<string[]>([])

  // Initialize with top 3 drugs once data is loaded
  useEffect(() => {
    if (drugStats && drugStats.length > 0 && selectedMeds.length === 0) {
      setSelectedMeds(drugStats.slice(0, 3).map(d => d.drug))
    }
  }, [drugStats, selectedMeds.length])

  const toggleMedication = (drug: string) => {
    if (selectedMeds.includes(drug)) {
      if (selectedMeds.length > 1) {
        setSelectedMeds(selectedMeds.filter((m) => m !== drug))
      }
    } else {
      if (selectedMeds.length < 4) {
        setSelectedMeds([...selectedMeds, drug])
      }
    }
  }

  const selectedMedications = drugStats?.filter((med) => selectedMeds.includes(med.drug)) ?? []

  if (isLoading) {
    return <div className="text-center py-8">Loading medications...</div>
  }

  if (!drugStats || drugStats.length === 0) {
    return <div className="text-center py-8">No medication data available</div>
  }

  return (
    <div>
      {/* Medication Selector */}
      <Card className="mb-8 border-border/40 bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Select Medications to Compare</h2>
        <div className="flex flex-wrap gap-3">
          {drugStats.slice(0, 8).map((drug) => (
            <Button
              key={drug.drug}
              variant={selectedMeds.includes(drug.drug) ? "default" : "outline"}
              onClick={() => toggleMedication(drug.drug)}
              className="gap-2"
            >
              {selectedMeds.includes(drug.drug) && <Check className="h-4 w-4" />}
              {drug.drug}
              <span className="ml-1 text-xs opacity-70">({drug.count})</span>
            </Button>
          ))}
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{selectedMeds.length}/4 medications selected</p>
      </Card>

      {/* Comparison Table */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
          <TabsTrigger value="side-effects">Side Effects</TabsTrigger>
          <TabsTrigger value="cost">Cost & Availability</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.drug} className="border-border/40 bg-card p-6">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{med.drug}</h3>
                    <p className="text-sm text-muted-foreground">{med.count} experiences</p>
                  </div>
                  <Badge variant="secondary">
                    {med.avgCostPerMonth ? `$${Math.round(med.avgCostPerMonth)}` : 'N/A'}
                  </Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Avg. Weight Loss</span>
                      <span className="font-semibold text-primary">
                        {med.avgWeightLoss ? `${med.avgWeightLoss.toFixed(1)}%` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Recommendation</span>
                      <span className="font-semibold">
                        {med.avgRecommendationScore ? `${Math.round(med.avgRecommendationScore * 100)}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${(med.avgRecommendationScore ?? 0) * 100}%` }}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">User Reports</span>
                      <span className="font-semibold">{med.count.toLocaleString()}</span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Avg. Duration</div>
                    <p className="text-sm font-medium">
                      {med.avgDurationWeeks ? `${Math.round(med.avgDurationWeeks / 4.33)} months` : 'N/A'}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="effectiveness">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.drug} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.drug}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Weight Loss</span>
                    </div>
                    <div className="text-2xl font-bold text-primary">
                      {med.avgWeightLoss ? `${med.avgWeightLoss.toFixed(1)}%` : 'N/A'}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Average over {med.avgDurationWeeks ? Math.round(med.avgDurationWeeks / 4.33) : 'N/A'} months
                    </p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Recommendation Score</div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${(med.avgRecommendationScore ?? 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold">
                        {med.avgRecommendationScore ? `${Math.round(med.avgRecommendationScore * 100)}%` : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-medium">Quality of Life</div>
                    <div className="text-sm text-muted-foreground">
                      {med.avgSentimentPre !== null && med.avgSentimentPost !== null ? (
                        <span>
                          {Math.round(med.avgSentimentPre * 100)}% → {Math.round(med.avgSentimentPost * 100)}%
                        </span>
                      ) : 'N/A'}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border/40">
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <div className="text-muted-foreground">Plateau Rate</div>
                        <div className="font-semibold">{Math.round(med.plateauRate)}%</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Rebound Rate</div>
                        <div className="font-semibold">{Math.round(med.reboundRate)}%</div>
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="side-effects">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.drug} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.drug}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 text-sm font-medium">Most Common Side Effects</div>
                    <ul className="space-y-1">
                      {med.commonSideEffects.slice(0, 5).map((effect) => (
                        <li key={effect.name} className="flex items-start gap-2 text-sm">
                          <X className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                          <div className="flex-1">
                            <span className="text-muted-foreground capitalize">{effect.name}</span>
                            <span className="ml-2 text-xs">({Math.round(effect.percentage)}%)</span>
                          </div>
                        </li>
                      ))}
                      {med.commonSideEffects.length === 0 && (
                        <li className="text-sm text-muted-foreground">No data available</li>
                      )}
                    </ul>
                  </div>

                  <div className="pt-4 border-t border-border/40">
                    <div className="text-sm font-medium mb-2">Severity Distribution</div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Mild</span>
                        <span className="font-semibold">{Math.round(med.sideEffectSeverity.mild)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Moderate</span>
                        <span className="font-semibold">{Math.round(med.sideEffectSeverity.moderate)}%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Severe</span>
                        <span className="font-semibold text-destructive">
                          {Math.round(med.sideEffectSeverity.severe)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border border-border/40 bg-muted/30 p-3">
                    <p className="text-xs text-muted-foreground">
                      Based on {med.count.toLocaleString()} user reports
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="cost">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.drug} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.drug}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Monthly Cost</span>
                    </div>
                    <div className="text-2xl font-bold">
                      ${med.avgCostPerMonth ? Math.round(med.avgCostPerMonth) : 'N/A'}
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Without insurance</p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Insurance Coverage</div>
                    <div className="text-2xl font-bold text-primary">
                      {Math.round(med.insuranceCoverage)}%
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">of users have coverage</p>
                  </div>

                  <div className="pt-4 border-t border-border/40">
                    <div className="text-sm font-medium mb-2">Drug Sources</div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Brand</span>
                        <span className="font-semibold">{med.drugSources.brand}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Compounded</span>
                        <span className="font-semibold">{med.drugSources.compounded}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground">Out-of-Pocket</span>
                        <span className="font-semibold">{med.drugSources.outOfPocket}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <Users className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Access Issues</span>
                    </div>
                    <div className="text-lg font-semibold">
                      {Math.round(med.pharmacyAccessIssues)}%
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      reported difficulty finding medication
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
