/**
 * Mock data functions - TO BE REPLACED WITH tRPC APIs
 *
 * These functions return mock data that matches the structure of what will come from
 * the database. Replace these with actual tRPC API calls once the backend is ready.
 */

import {
  DrugStats,
  LocationData,
  DemographicData,
  ExperienceCard,
  ExtractedFeature,
} from "./types"

/**
 * Get aggregated statistics for all drugs
 * TODO: Replace with tRPC query
 */
export async function getAllDrugStats(): Promise<DrugStats[]> {
  // Mock data based on the real drugs we have in the database
  return [
    {
      drug: "Wegovy",
      count: 209,
      avgWeightLoss: 16.8,
      avgWeightLossLbs: 28.5,
      avgDurationWeeks: 24,
      avgCostPerMonth: 1350,
      avgSentimentPre: 0.35,
      avgSentimentPost: 0.78,
      avgRecommendationScore: 0.82,
      insuranceCoverage: 45,
      commonSideEffects: [
        { name: "nausea", count: 98, percentage: 47 },
        { name: "vomiting", count: 65, percentage: 31 },
        { name: "diarrhea", count: 58, percentage: 28 },
      ],
      sideEffectSeverity: { mild: 45, moderate: 40, severe: 15 },
      drugSources: { brand: 180, compounded: 15, outOfPocket: 10, other: 4 },
      pharmacyAccessIssues: 28,
      plateauRate: 22,
      reboundRate: 8,
    },
    {
      drug: "Mounjaro",
      count: 123,
      avgWeightLoss: 18.2,
      avgWeightLossLbs: 32.1,
      avgDurationWeeks: 22,
      avgCostPerMonth: 1050,
      avgSentimentPre: 0.38,
      avgSentimentPost: 0.82,
      avgRecommendationScore: 0.86,
      insuranceCoverage: 52,
      commonSideEffects: [
        { name: "nausea", count: 52, percentage: 42 },
        { name: "diarrhea", count: 38, percentage: 31 },
        { name: "decreased appetite", count: 45, percentage: 37 },
      ],
      sideEffectSeverity: { mild: 50, moderate: 38, severe: 12 },
      drugSources: { brand: 105, compounded: 10, outOfPocket: 5, other: 3 },
      pharmacyAccessIssues: 18,
      plateauRate: 18,
      reboundRate: 6,
    },
    {
      drug: "Ozempic",
      count: 102,
      avgWeightLoss: 14.3,
      avgWeightLossLbs: 24.8,
      avgDurationWeeks: 26,
      avgCostPerMonth: 950,
      avgSentimentPre: 0.40,
      avgSentimentPost: 0.75,
      avgRecommendationScore: 0.78,
      insuranceCoverage: 58,
      commonSideEffects: [
        { name: "nausea", count: 45, percentage: 44 },
        { name: "constipation", count: 32, percentage: 31 },
        { name: "fatigue", count: 28, percentage: 27 },
      ],
      sideEffectSeverity: { mild: 52, moderate: 35, severe: 13 },
      drugSources: { brand: 90, compounded: 8, outOfPocket: 3, other: 1 },
      pharmacyAccessIssues: 22,
      plateauRate: 25,
      reboundRate: 10,
    },
    {
      drug: "Zepbound",
      count: 98,
      avgWeightLoss: 20.5,
      avgWeightLossLbs: 35.2,
      avgDurationWeeks: 20,
      avgCostPerMonth: 1200,
      avgSentimentPre: 0.36,
      avgSentimentPost: 0.84,
      avgRecommendationScore: 0.88,
      insuranceCoverage: 48,
      commonSideEffects: [
        { name: "nausea", count: 42, percentage: 43 },
        { name: "diarrhea", count: 35, percentage: 36 },
        { name: "constipation", count: 28, percentage: 29 },
      ],
      sideEffectSeverity: { mild: 48, moderate: 40, severe: 12 },
      drugSources: { brand: 85, compounded: 8, outOfPocket: 4, other: 1 },
      pharmacyAccessIssues: 32,
      plateauRate: 15,
      reboundRate: 5,
    },
    {
      drug: "Saxenda",
      count: 55,
      avgWeightLoss: 7.2,
      avgWeightLossLbs: 12.5,
      avgDurationWeeks: 28,
      avgCostPerMonth: 1400,
      avgSentimentPre: 0.42,
      avgSentimentPost: 0.68,
      avgRecommendationScore: 0.65,
      insuranceCoverage: 35,
      commonSideEffects: [
        { name: "nausea", count: 28, percentage: 51 },
        { name: "headache", count: 18, percentage: 33 },
        { name: "diarrhea", count: 15, percentage: 27 },
      ],
      sideEffectSeverity: { mild: 40, moderate: 45, severe: 15 },
      drugSources: { brand: 48, compounded: 5, outOfPocket: 2, other: 0 },
      pharmacyAccessIssues: 15,
      plateauRate: 32,
      reboundRate: 18,
    },
  ]
}

/**
 * Get statistics for a specific drug
 * TODO: Replace with tRPC query
 */
export async function getDrugStats(drug: string): Promise<DrugStats | null> {
  const allStats = await getAllDrugStats()
  return allStats.find((s) => s.drug.toLowerCase() === drug.toLowerCase()) || null
}

/**
 * Get location-based cost and availability data
 * TODO: Replace with tRPC query
 */
export async function getLocationData(): Promise<LocationData[]> {
  return [
    {
      location: "California",
      count: 285,
      avgCost: 1180,
      pharmacyAccessIssues: 22,
      topDrugs: [
        { drug: "Wegovy", count: 85 },
        { drug: "Mounjaro", count: 72 },
        { drug: "Ozempic", count: 65 },
      ],
    },
    {
      location: "Texas",
      count: 198,
      avgCost: 920,
      pharmacyAccessIssues: 18,
      topDrugs: [
        { drug: "Ozempic", count: 62 },
        { drug: "Wegovy", count: 58 },
        { drug: "Mounjaro", count: 42 },
      ],
    },
    {
      location: "New York",
      count: 176,
      avgCost: 1250,
      pharmacyAccessIssues: 25,
      topDrugs: [
        { drug: "Wegovy", count: 55 },
        { drug: "Zepbound", count: 48 },
        { drug: "Mounjaro", count: 38 },
      ],
    },
    {
      location: "Florida",
      count: 162,
      avgCost: 950,
      pharmacyAccessIssues: 20,
      topDrugs: [
        { drug: "Ozempic", count: 52 },
        { drug: "Wegovy", count: 48 },
        { drug: "Mounjaro", count: 35 },
      ],
    },
    {
      location: "Illinois",
      count: 128,
      avgCost: 980,
      pharmacyAccessIssues: 16,
      topDrugs: [
        { drug: "Mounjaro", count: 42 },
        { drug: "Ozempic", count: 38 },
        { drug: "Wegovy", count: 28 },
      ],
    },
  ]
}

/**
 * Get demographic breakdowns
 * TODO: Replace with tRPC query
 */
export async function getDemographicData(): Promise<DemographicData> {
  return {
    ageRanges: [
      { range: "18-29", count: 285 },
      { range: "30-39", count: 542 },
      { range: "40-49", count: 685 },
      { range: "50-59", count: 458 },
      { range: "60+", count: 218 },
    ],
    sexDistribution: [
      { sex: "female", count: 1456 },
      { sex: "male", count: 782 },
      { sex: "other", count: 45 },
      { sex: "unknown", count: 224 },
    ],
    topComorbidities: [
      { condition: "diabetes", count: 485 },
      { condition: "pcos", count: 342 },
      { condition: "hypertension", count: 298 },
      { condition: "sleep apnea", count: 186 },
      { condition: "hypothyroidism", count: 152 },
    ],
  }
}

/**
 * Get user experiences with filtering
 * TODO: Replace with tRPC query
 */
export async function getExperiences(filters?: {
  drug?: string
  minWeightLoss?: number
  maxCost?: number
  sex?: string
  limit?: number
  offset?: number
}): Promise<{ experiences: ExperienceCard[]; total: number }> {
  // Mock data - in reality this would query the database with filters
  const mockExperiences: ExperienceCard[] = [
    {
      id: "1",
      post_id: "1abc123",
      comment_id: null,
      summary:
        "Started Wegovy 6 months ago at 220 lbs, now down to 185 lbs. Nausea was rough the first month but mostly manageable now. Insurance covers it with $25 copay. Best decision I've made for my health.",
      primary_drug: "Wegovy",
      weightLoss: 35,
      weightLossUnit: "lbs",
      duration_weeks: 24,
      sentiment_post: 0.85,
      recommendation_score: 0.9,
      top_side_effects: ["nausea", "fatigue"],
      cost_per_month: 25,
      age: 42,
      sex: "female",
      location: "California",
      processed_at: "2025-01-15T10:30:00Z",
    },
    {
      id: "2",
      post_id: null,
      comment_id: "2def456",
      summary:
        "Mounjaro has been amazing. Lost 45 lbs in 5 months. Side effects were minimal - just some nausea in week 1-2. Paying $550/month out of pocket but worth every penny.",
      primary_drug: "Mounjaro",
      weightLoss: 45,
      weightLossUnit: "lbs",
      duration_weeks: 20,
      sentiment_post: 0.92,
      recommendation_score: 0.95,
      top_side_effects: ["nausea"],
      cost_per_month: 550,
      age: 38,
      sex: "male",
      location: "Texas",
      processed_at: "2025-01-14T15:45:00Z",
    },
    {
      id: "3",
      post_id: "3ghi789",
      comment_id: null,
      summary:
        "6 weeks on Ozempic. Down 12 lbs so far. Struggling with constipation and some fatigue but my A1C dropped from 8.2 to 6.5! Insurance approved it for diabetes management.",
      primary_drug: "Ozempic",
      weightLoss: 12,
      weightLossUnit: "lbs",
      duration_weeks: 6,
      sentiment_post: 0.72,
      recommendation_score: 0.8,
      top_side_effects: ["constipation", "fatigue"],
      cost_per_month: 10,
      age: 55,
      sex: "female",
      location: "Florida",
      processed_at: "2025-01-13T09:20:00Z",
    },
  ]

  return {
    experiences: mockExperiences,
    total: mockExperiences.length,
  }
}

/**
 * Get overall platform statistics
 * TODO: Replace with tRPC query
 */
export async function getPlatformStats(): Promise<{
  totalExperiences: number
  totalDrugs: number
  avgWeightLoss: number
  statesTracked: number
  countriesTracked: number
}> {
  return {
    totalExperiences: 2507,
    totalDrugs: 8,
    avgWeightLoss: 14.2,
    statesTracked: 48,
    countriesTracked: 12,
  }
}

/**
 * Get trend data over time
 * TODO: Replace with tRPC query
 */
export async function getTrendData(): Promise<
  Array<{
    month: string
    experiences: number
    avgWeightLoss: number
  }>
> {
  return [
    { month: "Aug", experiences: 215, avgWeightLoss: 13.8 },
    { month: "Sep", experiences: 298, avgWeightLoss: 14.1 },
    { month: "Oct", experiences: 385, avgWeightLoss: 14.3 },
    { month: "Nov", experiences: 456, avgWeightLoss: 14.5 },
    { month: "Dec", experiences: 542, avgWeightLoss: 14.2 },
    { month: "Jan", experiences: 611, avgWeightLoss: 14.0 },
  ]
}
