"use client"

import { useState } from "react"
import { Navigation } from "@/components/navigation"
import { Footer } from "@/components/footer"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { TrendingDown, DollarSign, AlertCircle, Check, X, Users, Target } from "lucide-react"
import { PredictionInput, PredictionResult, Sex } from "@/lib/types"

// Mock recommendation function - TO BE REPLACED with tRPC API
async function getRecommendations(input: PredictionInput): Promise<PredictionResult[]> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 1500))

  // Mock recommendation results
  return [
    {
      drug: "Mounjaro",
      matchScore: 92,
      expectedWeightLoss: {
        min: 35,
        max: 55,
        avg: 45,
        unit: input.weightUnit,
      },
      successRate: 85,
      estimatedCost: input.hasInsurance ? 25 : 1050,
      sideEffectProbability: [
        { effect: "nausea", probability: 42, severity: "moderate" },
        { effect: "diarrhea", probability: 31, severity: "mild" },
      ],
      similarUserCount: 45,
      pros: [
        "Highest predicted weight loss for your profile",
        "Strong success rate among similar users",
        "Manageable side effect profile",
      ],
      cons: ["Higher cost without insurance", "Weekly injections required"],
    },
    {
      drug: "Wegovy",
      matchScore: 88,
      expectedWeightLoss: {
        min: 30,
        max: 50,
        avg: 40,
        unit: input.weightUnit,
      },
      successRate: 82,
      estimatedCost: input.hasInsurance ? 25 : 1350,
      sideEffectProbability: [
        { effect: "nausea", probability: 47, severity: "moderate" },
        { effect: "vomiting", probability: 31, severity: "moderate" },
      ],
      similarUserCount: 58,
      pros: [
        "FDA approved for weight loss",
        "Strong track record",
        "Good insurance coverage",
      ],
      cons: ["Higher nausea rate", "Potential supply issues"],
    },
    {
      drug: "Ozempic",
      matchScore: 75,
      expectedWeightLoss: {
        min: 25,
        max: 40,
        avg: 32,
        unit: input.weightUnit,
      },
      successRate: 78,
      estimatedCost: input.hasInsurance ? 10 : 950,
      sideEffectProbability: [
        { effect: "nausea", probability: 44, severity: "mild" },
        { effect: "constipation", probability: 31, severity: "mild" },
      ],
      similarUserCount: 38,
      pros: ["Lower cost", "Good availability", "Fewer severe side effects"],
      cons: ["Moderate weight loss compared to others", "Not FDA approved specifically for weight loss"],
    },
  ]
}

const RecommendationsPage = () => {
  const [formData, setFormData] = useState<Partial<PredictionInput>>({
    weightUnit: "lbs",
    country: "USA",
    hasInsurance: false,
    comorbidities: [],
    sideEffectConcerns: [],
  })
  const [recommendations, setRecommendations] = useState<PredictionResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const commonComorbidities = ["diabetes", "pcos", "hypertension", "sleep apnea", "hypothyroidism"]
  const commonSideEffects = ["nausea", "vomiting", "diarrhea", "constipation", "fatigue"]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrors({})

    // Validation
    const newErrors: Record<string, string> = {}
    if (!formData.currentWeight) newErrors.currentWeight = "Current weight is required"
    if (!formData.goalWeight) newErrors.goalWeight = "Goal weight is required"
    if (!formData.age) newErrors.age = "Age is required"
    if (!formData.sex) newErrors.sex = "Gender is required"

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setLoading(true)
    try {
      const results = await getRecommendations(formData as PredictionInput)
      setRecommendations(results)
      window.scrollTo({ top: document.getElementById("results")?.offsetTop, behavior: "smooth" })
    } catch (error) {
      console.error("Recommendation error:", error)
    } finally {
      setLoading(false)
    }
  }

  const toggleComorbidity = (condition: string) => {
    const current = formData.comorbidities || []
    if (current.includes(condition)) {
      setFormData({
        ...formData,
        comorbidities: current.filter((c) => c !== condition),
      })
    } else {
      setFormData({
        ...formData,
        comorbidities: [...current, condition],
      })
    }
  }

  const toggleSideEffect = (effect: string) => {
    const current = formData.sideEffectConcerns || []
    if (current.includes(effect)) {
      setFormData({
        ...formData,
        sideEffectConcerns: current.filter((e) => e !== effect),
      })
    } else {
      setFormData({
        ...formData,
        sideEffectConcerns: [...current, effect],
      })
    }
  }

  return (
    <div className="min-h-screen relative">
      {/* Coming Soon Scrim Overlay */}
      <div className="pointer-events-none fixed inset-0 z-[9999] h-screen w-screen backdrop-blur-[2px] flex items-center justify-center">
        <div className="pointer-events-auto">
          <div className="relative overflow-hidden rounded-2xl border border-border/40 px-8 py-6 shadow-2xl" style={{background: 'linear-gradient(135deg, oklch(0.319 0.462 296.0 / 0.98), oklch(0.461 0.534 292.8 / 0.98))'}}>
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 animate-pulse rounded-full bg-white"></div>
              <span className="relative inline-block text-lg font-semibold tracking-tight">
                <span className="text-white">Coming soon!</span>
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent bg-[length:200%_100%] animate-[shimmer_2s_ease-in-out_infinite] bg-clip-text"></span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <Navigation />

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="mb-3 text-4xl font-bold">Recommend for Me</h1>
          <p className="text-lg text-muted-foreground">
            Find the best drug for your profile based on similar user experiences
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <Card className="mb-8 border-border/40 bg-card p-6">
            <h2 className="mb-6 text-xl font-semibold">Tell us about yourself</h2>

            <div className="grid gap-6 md:grid-cols-2">
              {/* Current Weight */}
              <div className="space-y-2">
                <Label htmlFor="currentWeight">
                  Current Weight <span className="text-destructive">*</span>
                </Label>
                <div className="flex gap-2">
                  <Input
                    id="currentWeight"
                    type="number"
                    placeholder="200"
                    value={formData.currentWeight || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, currentWeight: parseFloat(e.target.value) })
                    }
                    className={errors.currentWeight ? "border-destructive" : ""}
                  />
                  <Select
                    value={formData.weightUnit}
                    onValueChange={(value: "lbs" | "kg") =>
                      setFormData({ ...formData, weightUnit: value })
                    }
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="lbs">lbs</SelectItem>
                      <SelectItem value="kg">kg</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {errors.currentWeight && (
                  <p className="text-sm text-destructive">{errors.currentWeight}</p>
                )}
              </div>

              {/* Goal Weight */}
              <div className="space-y-2">
                <Label htmlFor="goalWeight">
                  Goal Weight <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="goalWeight"
                  type="number"
                  placeholder="160"
                  value={formData.goalWeight || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, goalWeight: parseFloat(e.target.value) })
                  }
                  className={errors.goalWeight ? "border-destructive" : ""}
                />
                {errors.goalWeight && (
                  <p className="text-sm text-destructive">{errors.goalWeight}</p>
                )}
              </div>

              {/* Age */}
              <div className="space-y-2">
                <Label htmlFor="age">
                  Age <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="age"
                  type="number"
                  placeholder="35"
                  value={formData.age || ""}
                  onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) })}
                  className={errors.age ? "border-destructive" : ""}
                />
                {errors.age && <p className="text-sm text-destructive">{errors.age}</p>}
              </div>

              {/* Gender */}
              <div className="space-y-2">
                <Label htmlFor="sex">
                  Gender <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={formData.sex}
                  onValueChange={(value: Sex) => setFormData({ ...formData, sex: value })}
                >
                  <SelectTrigger id="sex" className={errors.sex ? "border-destructive" : ""}>
                    <SelectValue placeholder="Select gender" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="ftm">FTM</SelectItem>
                    <SelectItem value="mtf">MTF</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                {errors.sex && <p className="text-sm text-destructive">{errors.sex}</p>}
              </div>

              {/* State */}
              <div className="space-y-2">
                <Label htmlFor="state">State (optional)</Label>
                <Input
                  id="state"
                  placeholder="California"
                  value={formData.state || ""}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                />
              </div>

              {/* Max Budget */}
              <div className="space-y-2">
                <Label htmlFor="maxBudget">Max Monthly Budget (optional)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                    $
                  </span>
                  <Input
                    id="maxBudget"
                    type="number"
                    placeholder="500"
                    value={formData.maxBudget || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, maxBudget: parseFloat(e.target.value) || null })
                    }
                    className="pl-7"
                  />
                </div>
              </div>
            </div>

            {/* Insurance */}
            <div className="mt-6 space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="hasInsurance"
                  checked={formData.hasInsurance}
                  onCheckedChange={(checked) =>
                    setFormData({ ...formData, hasInsurance: checked as boolean })
                  }
                />
                <Label htmlFor="hasInsurance" className="cursor-pointer">
                  I have health insurance
                </Label>
              </div>

              {formData.hasInsurance && (
                <div className="space-y-2">
                  <Label htmlFor="insuranceProvider">Insurance Provider (optional)</Label>
                  <Input
                    id="insuranceProvider"
                    placeholder="Blue Cross, UnitedHealthcare, etc."
                    value={formData.insuranceProvider || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, insuranceProvider: e.target.value })
                    }
                  />
                </div>
              )}
            </div>

            {/* Comorbidities */}
            <div className="mt-6 space-y-2">
              <Label>Pre-existing Conditions (optional)</Label>
              <p className="text-sm text-muted-foreground mb-3">
                Select any conditions that apply
              </p>
              <div className="flex flex-wrap gap-2">
                {commonComorbidities.map((condition) => (
                  <Button
                    key={condition}
                    type="button"
                    variant={(formData.comorbidities || []).includes(condition) ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleComorbidity(condition)}
                    className="capitalize"
                  >
                    {(formData.comorbidities || []).includes(condition) && (
                      <Check className="mr-1 h-3 w-3" />
                    )}
                    {condition}
                  </Button>
                ))}
              </div>
            </div>

            {/* Side Effect Concerns */}
            <div className="mt-6 space-y-2">
              <Label>Side Effect Concerns (optional)</Label>
              <p className="text-sm text-muted-foreground mb-3">
                Select side effects you want to avoid
              </p>
              <div className="flex flex-wrap gap-2">
                {commonSideEffects.map((effect) => (
                  <Button
                    key={effect}
                    type="button"
                    variant={(formData.sideEffectConcerns || []).includes(effect) ? "default" : "outline"}
                    size="sm"
                    onClick={() => toggleSideEffect(effect)}
                    className="capitalize"
                  >
                    {(formData.sideEffectConcerns || []).includes(effect) && (
                      <Check className="mr-1 h-3 w-3" />
                    )}
                    {effect}
                  </Button>
                ))}
              </div>
            </div>

            <div className="mt-8">
              <Button type="submit" size="lg" disabled={loading} className="w-full md:w-auto">
                {loading ? "Analyzing..." : "Get Recommendations"}
              </Button>
            </div>
          </Card>
        </form>

        {/* Results */}
        {recommendations && (
          <div id="results" className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <Target className="h-8 w-8 text-primary" />
              <div>
                <h2 className="text-2xl font-bold">Your Recommendations</h2>
                <p className="text-muted-foreground">
                  Based on {recommendations.reduce((sum, p) => sum + p.similarUserCount, 0)} similar user
                  experiences
                </p>
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              {recommendations.map((recommendation, index) => (
                <Card
                  key={recommendation.drug}
                  className={`border-border/40 bg-card p-6 relative ${
                    index === 0 ? "ring-2 ring-primary" : ""
                  }`}
                >
                  {index === 0 && (
                    <Badge className="absolute -top-3 left-1/2 -translate-x-1/2">
                      Best Match
                    </Badge>
                  )}

                  <div className="mb-4">
                    <h3 className="text-2xl font-bold mb-2">{recommendation.drug}</h3>
                    <div className="flex items-center gap-2">
                      <div className="flex-1">
                        <div className="text-xs text-muted-foreground mb-1">Match Score</div>
                        <Progress value={recommendation.matchScore} className="h-2" />
                      </div>
                      <div className="text-2xl font-bold text-primary">{recommendation.matchScore}%</div>
                    </div>
                  </div>

                  {/* Expected Weight Loss */}
                  <div className="mb-4 pb-4 border-b border-border/40">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingDown className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Expected Weight Loss</span>
                    </div>
                    <div className="text-3xl font-bold text-primary">
                      {recommendation.expectedWeightLoss.min}-{recommendation.expectedWeightLoss.max}{" "}
                      {recommendation.expectedWeightLoss.unit}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Average: {recommendation.expectedWeightLoss.avg} {recommendation.expectedWeightLoss.unit}
                    </p>
                  </div>

                  {/* Success Rate */}
                  <div className="mb-4 pb-4 border-b border-border/40">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Success Rate</span>
                    </div>
                    <div className="text-2xl font-bold">{recommendation.successRate}%</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Based on {recommendation.similarUserCount} similar users
                    </p>
                  </div>

                  {/* Cost */}
                  {recommendation.estimatedCost && (
                    <div className="mb-4 pb-4 border-b border-border/40">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Estimated Monthly Cost</span>
                      </div>
                      <div className="text-2xl font-bold">${recommendation.estimatedCost}</div>
                    </div>
                  )}

                  {/* Side Effects */}
                  <div className="mb-4 pb-4 border-b border-border/40">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="h-4 w-4 text-destructive" />
                      <span className="text-sm font-medium">Common Side Effects</span>
                    </div>
                    <div className="space-y-2">
                      {recommendation.sideEffectProbability.map((se) => (
                        <div key={se.effect} className="flex items-center justify-between text-xs">
                          <span className="capitalize text-muted-foreground">{se.effect}</span>
                          <span className="font-semibold">{se.probability}%</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Pros */}
                  <div className="mb-4">
                    <div className="text-sm font-medium mb-2">Pros</div>
                    <ul className="space-y-1">
                      {recommendation.pros.map((pro, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs">
                          <Check className="h-3 w-3 text-primary shrink-0 mt-0.5" />
                          <span className="text-muted-foreground">{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Cons */}
                  <div>
                    <div className="text-sm font-medium mb-2">Cons</div>
                    <ul className="space-y-1">
                      {recommendation.cons.map((con, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs">
                          <X className="h-3 w-3 text-destructive shrink-0 mt-0.5" />
                          <span className="text-muted-foreground">{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </Card>
              ))}
            </div>

            <Card className="border-border/40 bg-muted/30 p-6">
              <p className="text-sm text-muted-foreground">
                <strong>Disclaimer:</strong> These recommendations are based on aggregated user
                experiences and should not replace medical advice. Always consult with your
                healthcare provider before starting any drug.
              </p>
            </Card>
          </div>
        )}
      </div>

      <Footer />
    </div>
  )
}

export default RecommendationsPage
