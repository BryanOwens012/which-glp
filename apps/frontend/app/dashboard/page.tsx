"use client"

import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  TrendingUp,
  TrendingDown,
  Users,
  MessageSquare,
  MapPin,
  AlertTriangle,
  DollarSign,
  Activity,
} from "lucide-react"

// Note: Metadata cannot be exported from client components
// For SEO, consider creating a separate layout.tsx or page.tsx wrapper
import {
  Bar,
  BarChart,
  Line,
  LineChart,
  Pie,
  PieChart,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"

// Mock data for charts
const weightLossData = [
  { drug: "Zepbound", avgLoss: 20.5 },
  { drug: "Mounjaro", avgLoss: 18.2 },
  { drug: "Wegovy", avgLoss: 16.8 },
  { drug: "Ozempic", avgLoss: 14.3 },
  { drug: "Saxenda", avgLoss: 7.2 },
]

const timelineData = [
  { month: "Jan", reviews: 1200, mentions: 3400 },
  { month: "Feb", reviews: 1450, mentions: 3800 },
  { month: "Mar", reviews: 1680, mentions: 4200 },
  { month: "Apr", reviews: 1920, mentions: 4600 },
  { month: "May", reviews: 2100, mentions: 5100 },
  { month: "Jun", reviews: 2350, mentions: 5800 },
]

const sideEffectData = [
  { name: "Nausea", value: 42, color: "hsl(var(--chart-1))" },
  { name: "Diarrhea", value: 28, color: "hsl(var(--chart-2))" },
  { name: "Constipation", value: 18, color: "hsl(var(--chart-3))" },
  { name: "Fatigue", value: 12, color: "hsl(var(--chart-4))" },
]

const locationData = [
  { city: "New York, NY", avgCost: 1250, reviews: 890 },
  { city: "Los Angeles, CA", avgCost: 1180, reviews: 756 },
  { city: "Chicago, IL", avgCost: 980, reviews: 623 },
  { city: "Houston, TX", avgCost: 920, reviews: 542 },
  { city: "Phoenix, AZ", avgCost: 890, reviews: 478 },
]

const sentimentData = [
  { drug: "Zepbound", positive: 78, neutral: 15, negative: 7 },
  { drug: "Mounjaro", positive: 75, neutral: 18, negative: 7 },
  { drug: "Wegovy", positive: 72, neutral: 20, negative: 8 },
  { drug: "Ozempic", positive: 68, neutral: 22, negative: 10 },
  { drug: "Saxenda", positive: 58, neutral: 28, negative: 14 },
]

const DashboardPage = () => {
  return (
    <div className="min-h-screen">
      <Navigation />

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="mb-3 text-4xl font-bold">Data Dashboard</h1>
          <p className="text-lg text-muted-foreground">
            Real-time insights from thousands of GLP-1 user experiences across social media
          </p>
        </div>

        {/* Key Metrics */}
        <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-border/40 bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Reviews</p>
                <p className="mt-1 text-3xl font-bold">15,340</p>
                <div className="mt-2 flex items-center gap-1 text-sm text-primary">
                  <TrendingUp className="h-4 w-4" />
                  <span>+12% this month</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <MessageSquare className="h-6 w-6 text-primary" />
              </div>
            </div>
          </Card>

          <Card className="border-border/40 bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active Users</p>
                <p className="mt-1 text-3xl font-bold">8,920</p>
                <div className="mt-2 flex items-center gap-1 text-sm text-primary">
                  <TrendingUp className="h-4 w-4" />
                  <span>+8% this month</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Users className="h-6 w-6 text-primary" />
              </div>
            </div>
          </Card>

          <Card className="border-border/40 bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg. Weight Loss</p>
                <p className="mt-1 text-3xl font-bold">14.2%</p>
                <div className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                  <Activity className="h-4 w-4" />
                  <span>Across all drugs</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <TrendingDown className="h-6 w-6 text-primary" />
              </div>
            </div>
          </Card>

          <Card className="border-border/40 bg-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Shortage Alerts</p>
                <p className="mt-1 text-3xl font-bold">3</p>
                <div className="mt-2 flex items-center gap-1 text-sm text-destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Active alerts</span>
                </div>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-destructive/10">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
            </div>
          </Card>
        </div>

        {/* Main Dashboard Content */}
        <Tabs defaultValue="effectiveness" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
            <TabsTrigger value="side-effects">Side Effects</TabsTrigger>
            <TabsTrigger value="location">Location Data</TabsTrigger>
          </TabsList>

          <TabsContent value="effectiveness" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Weight Loss Comparison */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Average Weight Loss by Drug</h3>
                <p className="mb-6 text-sm text-muted-foreground">Based on 6-month user-reported outcomes</p>
                <ChartContainer
                  config={{
                    avgLoss: {
                      label: "Avg Weight Loss %",
                      color: "hsl(var(--primary))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={weightLossData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="drug" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <ChartTooltip content={<ChartTooltipContent />} />
                      <Bar dataKey="avgLoss" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </Card>

              {/* Sentiment Analysis */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">User Sentiment by Drug</h3>
                <p className="mb-6 text-sm text-muted-foreground">Positive, neutral, and negative reviews</p>
                <div className="space-y-4">
                  {sentimentData.map((drug) => (
                    <div key={drug.drug}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="font-medium">{drug.drug}</span>
                        <span className="text-muted-foreground">{drug.positive}% positive</span>
                      </div>
                      <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
                        <div className="bg-primary" style={{ width: `${drug.positive}%` }} />
                        <div className="bg-muted-foreground/30" style={{ width: `${drug.neutral}%` }} />
                        <div className="bg-destructive" style={{ width: `${drug.negative}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-6 flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-primary" />
                    <span className="text-muted-foreground">Positive</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-muted-foreground/30" />
                    <span className="text-muted-foreground">Neutral</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-destructive" />
                    <span className="text-muted-foreground">Negative</span>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <Card className="border-border/40 bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold">Review Volume Over Time</h3>
              <p className="mb-6 text-sm text-muted-foreground">Monthly reviews and social media mentions</p>
              <ChartContainer
                config={{
                  reviews: {
                    label: "Reviews",
                    color: "hsl(var(--primary))",
                  },
                  mentions: {
                    label: "Social Mentions",
                    color: "hsl(var(--chart-2))",
                  },
                }}
                className="h-[400px]"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timelineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="reviews"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={{ fill: "hsl(var(--primary))" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="mentions"
                      stroke="hsl(var(--chart-2))"
                      strokeWidth={2}
                      dot={{ fill: "hsl(var(--chart-2))" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </Card>

            <div className="grid gap-6 md:grid-cols-3">
              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Trending Up</h4>
                <p className="mb-1 text-2xl font-bold">Zepbound</p>
                <div className="flex items-center gap-1 text-sm text-primary">
                  <TrendingUp className="h-4 w-4" />
                  <span>+45% mentions this week</span>
                </div>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Most Discussed</h4>
                <p className="mb-1 text-2xl font-bold">Ozempic</p>
                <p className="text-sm text-muted-foreground">5,800 mentions this month</p>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Rising Concern</h4>
                <p className="mb-1 text-2xl font-bold">Shortages</p>
                <div className="flex items-center gap-1 text-sm text-destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <span>3 drugs affected</span>
                </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="side-effects" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Most Common Side Effects</h3>
                <p className="mb-6 text-sm text-muted-foreground">Reported across all GLP-1 medications</p>
                <ChartContainer
                  config={{
                    value: {
                      label: "Percentage",
                      color: "hsl(var(--primary))",
                    },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={sideEffectData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={100}
                        fill="hsl(var(--primary))"
                        dataKey="value"
                      >
                        {sideEffectData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Side Effect Details</h3>
                <p className="mb-6 text-sm text-muted-foreground">Frequency and severity by symptom</p>
                <div className="space-y-4">
                  {sideEffectData.map((effect) => (
                    <div key={effect.name} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{effect.name}</span>
                        <Badge variant="secondary">{effect.value}%</Badge>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div className="h-full bg-destructive" style={{ width: `${effect.value}%` }} />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Reported by {Math.round((effect.value / 100) * 15340)} users
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="location" className="space-y-6">
            <Card className="border-border/40 bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold">Cost by Location</h3>
              <p className="mb-6 text-sm text-muted-foreground">Average monthly cost and review volume by city</p>
              <div className="space-y-4">
                {locationData.map((location, index) => (
                  <div key={location.city} className="flex items-center gap-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="mb-1 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{location.city}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="font-semibold">${location.avgCost}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">{location.reviews}</span>
                          </div>
                        </div>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${(location.reviews / locationData[0].reviews) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-4 text-sm font-medium text-muted-foreground">Lowest Average Cost</h4>
                <p className="mb-1 text-2xl font-bold">Phoenix, AZ</p>
                <p className="text-lg text-primary">$890/month</p>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-4 text-sm font-medium text-muted-foreground">Highest Review Volume</h4>
                <p className="mb-1 text-2xl font-bold">New York, NY</p>
                <p className="text-lg text-primary">890 reviews</p>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default DashboardPage
