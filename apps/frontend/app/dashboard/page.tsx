"use client"

import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StatCard } from "@/components/stat-card"
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
import { trpc } from "@/lib/trpc"

const DashboardPage = () => {
  // Fetch all data using tRPC
  const { data: drugStats, isLoading: drugsLoading } = trpc.drugs.getAllStats.useQuery()
  const { data: locationData, isLoading: locationsLoading } = trpc.locations.getData.useQuery()
  const { data: demographicData, isLoading: demographicsLoading } = trpc.demographics.getData.useQuery()
  const { data: platformStats, isLoading: platformLoading } = trpc.platform.getStats.useQuery()
  const { data: trendData, isLoading: trendsLoading } = trpc.platform.getTrends.useQuery({ period: 'month' })

  const loading = drugsLoading || locationsLoading || demographicsLoading || platformLoading || trendsLoading

  if (loading) {
    return (
      <div className="min-h-screen">
        <Navigation />
        <div className="container mx-auto px-4 pt-24 pb-12">
          <div className="text-center">Loading dashboard...</div>
        </div>
      </div>
    )
  }

  // Prepare data for charts
  const weightLossData = drugStats?.map((d) => ({
      drug: d.drug,
      avgLoss: d.avgWeightLoss || 0,
    }))
    .sort((a, b) => b.avgLoss - a.avgLoss) ?? []

  const sentimentData = drugStats?.map((d) => ({
    drug: d.drug,
    positive: Math.round(((d.avgRecommendationScore || 0) * 100)),
    neutral: 15,
    negative: Math.round((1 - (d.avgRecommendationScore || 0)) * 100) - 15,
  })) ?? []

  // Aggregate side effects across all drugs
  const allSideEffects = drugStats
    ?.flatMap((d) => d.commonSideEffects || [])
    .reduce(
      (acc: Array<{ name: string; percentage: number }>, effect: { name: string; count: number; percentage: number }) => {
        const existing = acc.find((e: { name: string; percentage: number }) => e.name === effect.name)
        if (existing) {
          existing.percentage += effect.percentage
        } else {
          acc.push({ name: effect.name, percentage: effect.percentage })
        }
        return acc
      },
      [] as Array<{ name: string; percentage: number }>
    )
    .sort((a: { percentage: number }, b: { percentage: number }) => b.percentage - a.percentage)
    .slice(0, 5) ?? []

  const totalSideEffects = allSideEffects.reduce((sum: number, e: { percentage: number }) => sum + e.percentage, 0)
  const sideEffectChartData = allSideEffects.map((e: { name: string; percentage: number }, i: number) => ({
    name: e.name,
    value: Math.round((e.percentage / (totalSideEffects || 1)) * 100),
    color: `hsl(var(--chart-${(i % 5) + 1}))`,
  }))

  const chartColors = ["hsl(var(--chart-1))", "hsl(var(--chart-2))", "hsl(var(--chart-3))", "hsl(var(--chart-4))", "hsl(var(--chart-5))"]

  return (
    <div className="min-h-screen">
      <Navigation />

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="mb-3 text-4xl font-bold">Data Dashboard</h1>
          <p className="text-lg text-muted-foreground">
            Real-time insights from {platformStats?.totalExperiences.toLocaleString() ?? 0} GLP-1 user
            experiences across Reddit
          </p>
        </div>

        {/* Key Metrics */}
        <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Experiences"
            value={platformStats?.totalExperiences.toLocaleString() ?? "0"}
            subtitle="User experiences analyzed"
            icon={MessageSquare}
          />
          <StatCard
            title="Medications Tracked"
            value={platformStats?.uniqueDrugs ?? 0}
            subtitle="Different GLP-1 medications"
            icon={Activity}
          />
          <StatCard
            title="Avg. Weight Loss"
            value={`${Math.round(platformStats?.avgWeightLossPercentage ?? 0)}%`}
            subtitle="Across all medications"
            icon={TrendingDown}
            valueClassName="text-primary"
          />
          <StatCard
            title="Locations"
            value={platformStats?.locationsTracked ?? 0}
            subtitle="US states tracked"
            icon={MapPin}
          />
        </div>

        {/* Main Dashboard Content */}
        <Tabs defaultValue="effectiveness" className="w-full">
          <TabsList className="mb-6">
            <TabsTrigger value="effectiveness">Effectiveness</TabsTrigger>
            <TabsTrigger value="demographics">Demographics</TabsTrigger>
            <TabsTrigger value="side-effects">Side Effects</TabsTrigger>
            <TabsTrigger value="location">Cost by Location</TabsTrigger>
            <TabsTrigger value="trends">Trends</TabsTrigger>
          </TabsList>

          {/* Effectiveness Tab */}
          <TabsContent value="effectiveness" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Weight Loss Chart */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Average Weight Loss by Drug</h3>
                <p className="mb-6 text-sm text-muted-foreground">
                  Based on user-reported outcomes
                </p>
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

              {/* User Sentiment */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">User Sentiment by Drug</h3>
                <p className="mb-6 text-sm text-muted-foreground">
                  Recommendation rates and satisfaction
                </p>
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

            {/* Top Performers */}
            <div className="grid gap-6 md:grid-cols-3">
              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                  Highest Weight Loss
                </h4>
                <p className="mb-1 text-2xl font-bold">{weightLossData[0]?.drug}</p>
                <div className="text-lg text-primary">{weightLossData[0]?.avgLoss.toFixed(1)}%</div>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Most Recommended</h4>
                <p className="mb-1 text-2xl font-bold">
                  {
                    drugStats?.sort(
                      (a, b) => (b.avgRecommendationScore || 0) - (a.avgRecommendationScore || 0)
                    )[0]?.drug ?? 'N/A'
                  }
                </p>
                <div className="text-lg text-primary">
                  {Math.round(
                    (drugStats?.sort(
                      (a, b) => (b.avgRecommendationScore || 0) - (a.avgRecommendationScore || 0)
                    )[0]?.avgRecommendationScore || 0) * 100
                  )}
                  % recommend
                </div>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">
                  Best Insurance Coverage
                </h4>
                <p className="mb-1 text-2xl font-bold">
                  {drugStats?.sort((a, b) => b.insuranceCoverage - a.insuranceCoverage)[0]?.drug ?? 'N/A'}
                </p>
                <div className="text-lg text-primary">
                  {Math.round(
                    drugStats?.sort((a, b) => b.insuranceCoverage - a.insuranceCoverage)[0]
                      ?.insuranceCoverage ?? 0
                  )}
                  % coverage
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Demographics Tab */}
          <TabsContent value="demographics" className="space-y-6">
            {demographicData && (
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Age Distribution */}
                <Card className="border-border/40 bg-card p-6">
                  <h3 className="mb-4 text-lg font-semibold">Age Distribution</h3>
                  <p className="mb-6 text-sm text-muted-foreground">User age ranges</p>
                  <ChartContainer
                    config={{
                      count: { label: "Users", color: "hsl(var(--primary))" },
                    }}
                    className="h-[300px]"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={demographicData?.ageDistribution ?? []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="range" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <ChartTooltip content={<ChartTooltipContent />} />
                        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </Card>

                {/* Sex Distribution */}
                <Card className="border-border/40 bg-card p-6">
                  <h3 className="mb-4 text-lg font-semibold">Gender Distribution</h3>
                  <p className="mb-6 text-sm text-muted-foreground">User demographics</p>
                  <ChartContainer
                    config={{
                      count: { label: "Users", color: "hsl(var(--primary))" },
                    }}
                    className="h-[300px]"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={demographicData?.sexDistribution ?? []}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={(props: any) => {
                            const sex = props.sex === "unknown" ? "Unknown" : props.sex
                            return `${sex.charAt(0).toUpperCase() + sex.slice(1)}: ${props.count}`
                          }}
                          outerRadius={100}
                          fill="hsl(var(--primary))"
                          dataKey="count"
                        >
                          {demographicData?.sexDistribution.map((entry, index) => (
                            <Cell key={`sex-${entry.sex}-${index}`} fill={chartColors[index % chartColors.length]} />
                          ))}
                        </Pie>
                        <ChartTooltip content={<ChartTooltipContent />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </Card>

                {/* Comorbidities */}
                {/* Comorbidities data not yet available in database */}
                {/* <Card className="border-border/40 bg-card p-6 lg:col-span-2">
                  <h3 className="mb-4 text-lg font-semibold">Top Comorbidities</h3>
                  <p className="mb-6 text-sm text-muted-foreground">
                    Most commonly reported pre-existing conditions
                  </p>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
                    Coming soon
                  </div>
                </Card> */}
              </div>
            )}
          </TabsContent>

          {/* Side Effects Tab */}
          <TabsContent value="side-effects" className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Pie Chart */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Most Common Side Effects</h3>
                <p className="mb-6 text-sm text-muted-foreground">
                  Reported across all GLP-1 medications
                </p>
                <ChartContainer
                  config={{
                    value: { label: "Percentage", color: "hsl(var(--primary))" },
                  }}
                  className="h-[300px]"
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={sideEffectChartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={(props: any) => {
                          const name = props.name.charAt(0).toUpperCase() + props.name.slice(1)
                          return `${name}: ${props.value}%`
                        }}
                        outerRadius={100}
                        fill="hsl(var(--primary))"
                        dataKey="value"
                      >
                        {sideEffectChartData.map((entry, index) => (
                          <Cell key={`side-effect-${entry.name}-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <ChartTooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </Card>

              {/* Details */}
              <Card className="border-border/40 bg-card p-6">
                <h3 className="mb-4 text-lg font-semibold">Side Effect Details</h3>
                <p className="mb-6 text-sm text-muted-foreground">
                  Frequency across all user reports
                </p>
                <div className="space-y-4">
                  {allSideEffects.map((effect: { name: string; percentage: number }) => (
                    <div key={effect.name} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize">{effect.name}</span>
                        <span className="text-sm text-muted-foreground">{Math.round(effect.percentage)}% of users</span>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-destructive"
                          style={{ width: `${(effect.percentage / (allSideEffects[0]?.percentage || 1)) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </TabsContent>

          {/* Location Tab */}
          <TabsContent value="location" className="space-y-6">
            <Card className="border-border/40 bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold">Cost by Location</h3>
              <p className="mb-6 text-sm text-muted-foreground">
                Average monthly cost and experience volume by state
              </p>
              <div className="space-y-4">
                {locationData?.map((location, index) => (
                  <div key={location.location} className="flex items-center gap-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="mb-1 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{location.location}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-1">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="font-semibold">${location.avgCost}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground">{location.count}</span>
                          </div>
                        </div>
                      </div>
                      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full bg-primary"
                          style={{ width: `${locationData && locationData[0] ? (location.count / locationData[0].count) * 100 : 0}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-4 text-sm font-medium text-muted-foreground">
                  Lowest Average Cost
                </h4>
                <p className="mb-1 text-2xl font-bold">
                  {locationData?.sort((a, b) => (a.avgCost || 0) - (b.avgCost || 0))[0]?.location ?? 'N/A'}
                </p>
                <p className="text-lg text-primary">
                  ${locationData?.sort((a, b) => (a.avgCost || 0) - (b.avgCost || 0))[0]?.avgCost ?? 0}/month
                </p>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-4 text-sm font-medium text-muted-foreground">
                  Most Experiences
                </h4>
                <p className="mb-1 text-2xl font-bold">
                  {locationData?.sort((a, b) => b.count - a.count)[0]?.location ?? 'N/A'}
                </p>
                <p className="text-lg text-primary">
                  {locationData?.sort((a, b) => b.count - a.count)[0]?.count ?? 0} experiences
                </p>
              </Card>
            </div>
          </TabsContent>

          {/* Trends Tab */}
          <TabsContent value="trends" className="space-y-6">
            <Card className="border-border/40 bg-card p-6">
              <h3 className="mb-4 text-lg font-semibold">Experience Volume Over Time</h3>
              <p className="mb-6 text-sm text-muted-foreground">
                Monthly user experiences and average weight loss trends
              </p>
              <ChartContainer
                config={{
                  experiences: { label: "Experiences", color: "hsl(var(--primary))" },
                  avgWeightLoss: { label: "Avg Weight Loss %", color: "hsl(var(--chart-2))" },
                }}
                className="h-[400px]"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis
                      yAxisId="right"
                      orientation="right"
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={12}
                    />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="experiences"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={{ fill: "hsl(var(--primary))" }}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="avgWeightLoss"
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
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Growing Interest</h4>
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <p className="text-2xl font-bold">+48%</p>
                </div>
                <p className="text-sm text-muted-foreground">Since August</p>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Latest Month</h4>
                <p className="mb-1 text-2xl font-bold">{trendData && trendData.length > 0 ? (trendData[trendData.length - 1] as any)?.experiences ?? 0 : 0}</p>
                <p className="text-sm text-muted-foreground">New experiences</p>
              </Card>

              <Card className="border-border/40 bg-card p-6">
                <h4 className="mb-2 text-sm font-medium text-muted-foreground">Avg Weight Loss</h4>
                <p className="mb-1 text-2xl font-bold text-primary">
                  {trendData && trendData.length > 0 ? ((trendData[trendData.length - 1] as any)?.avgWeightLoss ?? 0).toFixed(1) : "0"}%
                </p>
                <p className="text-sm text-muted-foreground">Current month</p>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default DashboardPage
