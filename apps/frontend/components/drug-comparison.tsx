"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Check, X, TrendingUp, DollarSign, AlertCircle, Users } from "lucide-react"

// Mock data for GLP-1 medications
const medications = [
  {
    id: "ozempic",
    name: "Ozempic",
    genericName: "Semaglutide",
    manufacturer: "Novo Nordisk",
    avgWeightLoss: "12-15%",
    effectiveness: 4.5,
    sideEffects: 3.2,
    cost: "$$$",
    costPerMonth: 950,
    userRating: 4.3,
    totalReviews: 3420,
    availability: "High",
    dosing: "Weekly injection",
    commonSideEffects: ["Nausea", "Diarrhea", "Constipation", "Fatigue"],
    benefits: ["Proven weight loss", "Cardiovascular benefits", "Once weekly dosing"],
  },
  {
    id: "wegovy",
    name: "Wegovy",
    genericName: "Semaglutide",
    manufacturer: "Novo Nordisk",
    avgWeightLoss: "15-18%",
    effectiveness: 4.7,
    sideEffects: 3.5,
    cost: "$$$",
    costPerMonth: 1350,
    userRating: 4.5,
    totalReviews: 2890,
    availability: "Medium",
    dosing: "Weekly injection",
    commonSideEffects: ["Nausea", "Vomiting", "Diarrhea", "Stomach pain"],
    benefits: ["Highest weight loss", "FDA approved for weight loss", "Once weekly"],
  },
  {
    id: "mounjaro",
    name: "Mounjaro",
    genericName: "Tirzepatide",
    manufacturer: "Eli Lilly",
    avgWeightLoss: "15-20%",
    effectiveness: 4.8,
    sideEffects: 3.4,
    cost: "$$$",
    costPerMonth: 1050,
    userRating: 4.6,
    totalReviews: 2150,
    availability: "High",
    dosing: "Weekly injection",
    commonSideEffects: ["Nausea", "Diarrhea", "Decreased appetite", "Vomiting"],
    benefits: ["Dual action mechanism", "Excellent weight loss", "Good tolerability"],
  },
  {
    id: "zepbound",
    name: "Zepbound",
    genericName: "Tirzepatide",
    manufacturer: "Eli Lilly",
    avgWeightLoss: "18-22%",
    effectiveness: 4.9,
    sideEffects: 3.6,
    cost: "$$$",
    costPerMonth: 1200,
    userRating: 4.7,
    totalReviews: 1680,
    availability: "Medium",
    dosing: "Weekly injection",
    commonSideEffects: ["Nausea", "Diarrhea", "Constipation", "Abdominal pain"],
    benefits: ["Highest efficacy", "FDA approved for obesity", "Dual receptor action"],
  },
  {
    id: "saxenda",
    name: "Saxenda",
    genericName: "Liraglutide",
    manufacturer: "Novo Nordisk",
    avgWeightLoss: "5-8%",
    effectiveness: 3.8,
    sideEffects: 3.8,
    cost: "$$",
    costPerMonth: 1400,
    userRating: 3.9,
    totalReviews: 4200,
    availability: "High",
    dosing: "Daily injection",
    commonSideEffects: ["Nausea", "Diarrhea", "Constipation", "Headache"],
    benefits: ["Long track record", "Daily dosing flexibility", "Well studied"],
  },
]

export const DrugComparison = () => {
  const [selectedMeds, setSelectedMeds] = useState<string[]>(["ozempic", "wegovy", "mounjaro"])

  const toggleMedication = (id: string) => {
    if (selectedMeds.includes(id)) {
      if (selectedMeds.length > 1) {
        setSelectedMeds(selectedMeds.filter((m) => m !== id))
      }
    } else {
      if (selectedMeds.length < 4) {
        setSelectedMeds([...selectedMeds, id])
      }
    }
  }

  const selectedMedications = medications.filter((med) => selectedMeds.includes(med.id))

  return (
    <div>
      {/* Medication Selector */}
      <Card className="mb-8 border-border/40 bg-card p-6">
        <h2 className="mb-4 text-lg font-semibold">Select Medications to Compare</h2>
        <div className="flex flex-wrap gap-3">
          {medications.map((med) => (
            <Button
              key={med.id}
              variant={selectedMeds.includes(med.id) ? "default" : "outline"}
              onClick={() => toggleMedication(med.id)}
              className="gap-2"
            >
              {selectedMeds.includes(med.id) && <Check className="h-4 w-4" />}
              {med.name}
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
              <Card key={med.id} className="border-border/40 bg-card p-6">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{med.name}</h3>
                    <p className="text-sm text-muted-foreground">{med.genericName}</p>
                  </div>
                  <Badge variant="secondary">{med.cost}</Badge>
                </div>

                <div className="space-y-4">
                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Avg. Weight Loss</span>
                      <span className="font-semibold text-primary">{med.avgWeightLoss}</span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">User Rating</span>
                      <span className="font-semibold">{med.userRating}/5.0</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                      <div className="h-full bg-primary" style={{ width: `${(med.userRating / 5) * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Reviews</span>
                      <span className="font-semibold">{med.totalReviews.toLocaleString()}</span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Dosing</div>
                    <p className="text-sm font-medium">{med.dosing}</p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Availability</div>
                    <Badge variant={med.availability === "High" ? "default" : "secondary"}>{med.availability}</Badge>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="effectiveness">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.id} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.name}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Weight Loss</span>
                    </div>
                    <div className="text-2xl font-bold text-primary">{med.avgWeightLoss}</div>
                    <p className="mt-1 text-xs text-muted-foreground">Average over 6 months</p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Effectiveness Score</div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div className="h-full bg-primary" style={{ width: `${(med.effectiveness / 5) * 100}%` }} />
                      </div>
                      <span className="text-sm font-semibold">{med.effectiveness}/5</span>
                    </div>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-medium">Key Benefits</div>
                    <ul className="space-y-1">
                      {med.benefits.map((benefit, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                          <span className="text-muted-foreground">{benefit}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="side-effects">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {selectedMedications.map((med) => (
              <Card key={med.id} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.name}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-destructive" />
                      <span className="text-sm font-medium">Side Effect Severity</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                        <div className="h-full bg-destructive" style={{ width: `${(med.sideEffects / 5) * 100}%` }} />
                      </div>
                      <span className="text-sm font-semibold">{med.sideEffects}/5</span>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">Lower is better</p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-medium">Common Side Effects</div>
                    <ul className="space-y-1">
                      {med.commonSideEffects.map((effect, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm">
                          <X className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                          <span className="text-muted-foreground">{effect}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-lg border border-border/40 bg-muted/30 p-3">
                    <p className="text-xs text-muted-foreground">
                      Based on {med.totalReviews.toLocaleString()} user reports
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
              <Card key={med.id} className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-xl font-bold">{med.name}</h3>

                <div className="space-y-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <DollarSign className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Monthly Cost</span>
                    </div>
                    <div className="text-2xl font-bold">${med.costPerMonth}</div>
                    <p className="mt-1 text-xs text-muted-foreground">Without insurance</p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm text-muted-foreground">Cost Category</div>
                    <Badge variant="secondary" className="text-base">
                      {med.cost}
                    </Badge>
                  </div>

                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <Users className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Availability</span>
                    </div>
                    <Badge variant={med.availability === "High" ? "default" : "secondary"}>{med.availability}</Badge>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {med.availability === "High"
                        ? "Widely available at most pharmacies"
                        : "May have limited availability"}
                    </p>
                  </div>

                  <div>
                    <div className="mb-2 text-sm font-medium">Manufacturer</div>
                    <p className="text-sm text-muted-foreground">{med.manufacturer}</p>
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
