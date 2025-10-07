"use client"

import { useState, useEffect, useRef } from "react"
import { Navigation } from "@/components/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ExperienceCard as ExperienceCardComponent } from "@/components/experience-card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Search, Filter, Loader2, ArrowUpDown } from "lucide-react"
import { trpc } from "@/lib/trpc"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { RedditLink } from "@/components/reddit-link"
import { getRedditReference, formatDuration, formatCost } from "@/lib/types"
import { SortField, SortDirection, SORT_FIELD_LABELS, SORT_DIRECTION_TOOLTIPS, SortFieldType, SortDirectionType } from "@/lib/sort-types"

const ExperiencesPage = () => {
  // Filters
  const [selectedDrug, setSelectedDrug] = useState<string>("all")
  const [searchText, setSearchText] = useState("")
  const [debouncedSearchText, setDebouncedSearchText] = useState("")
  const [sortBy, setSortBy] = useState<SortFieldType>(SortField.DATE)
  const [sortOrder, setSortOrder] = useState<SortDirectionType>(SortDirection.DESC)
  const [selectedExperienceId, setSelectedExperienceId] = useState<string | null>(null)

  // Intersection observer ref for infinite scroll
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchText(searchText)
    }, 200)

    return () => clearTimeout(timer)
  }, [searchText])

  // Fetch experiences with infinite scroll
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading: experiencesLoading,
    isFetching,
  } = trpc.experiences.list.useInfiniteQuery(
    ({ pageParam = 0 }) => ({
      drug: selectedDrug !== "all" ? selectedDrug : undefined,
      search: debouncedSearchText || undefined,
      sortBy,
      sortOrder,
      limit: 20,
      offset: pageParam,
    }),
    {
      getNextPageParam: (lastPage, allPages) => {
        const loadedCount = allPages.reduce((sum, page) => sum + page.experiences.length, 0)
        return loadedCount < lastPage.total ? loadedCount : undefined
      },
      keepPreviousData: true, // Keep previous data while fetching new
    }
  )

  // Flatten all pages into single array
  const experiencesData = data
    ? {
        experiences: data.pages.flatMap((page) => page.experiences),
        total: data.pages[0]?.total ?? 0,
      }
    : { experiences: [], total: 0 }

  // Fetch drug stats for the filter dropdown
  const { data: drugs } = trpc.drugs.getAllStats.useQuery()

  // Fetch selected experience details
  const { data: selectedExperience } = trpc.experiences.getById.useQuery(
    { id: selectedExperienceId! },
    { enabled: !!selectedExperienceId }
  )

  // Intersection observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current || !hasNextPage || isFetchingNextPage) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          fetchNextPage()
        }
      },
      { threshold: 0.1 }
    )

    observer.observe(loadMoreRef.current)

    return () => observer.disconnect()
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  // Determine if we should show skeleton (initial load only, not filter changes)
  const showSkeleton = experiencesLoading && !data

  return (
    <div className="min-h-screen">
      <Navigation />

      <div className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="mb-3 text-4xl font-bold">User Experiences</h1>
          <p className="text-lg text-muted-foreground">
            Browse real user experiences with GLP-1 medications from Reddit
          </p>
        </div>

        {/* Filters */}
        <Card className="mb-8 border-border/40 bg-card p-6">
          <div className="mb-4 flex items-center gap-2">
            <Filter className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-lg font-semibold">Filters</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Search */}
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="search"
                  placeholder="Search experiences..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Drug Filter */}
            <div className="space-y-2">
              <Label htmlFor="drug">Medication</Label>
              <Select value={selectedDrug} onValueChange={setSelectedDrug}>
                <SelectTrigger id="drug">
                  <SelectValue placeholder="All medications" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All medications</SelectItem>
                  {drugs?.map((drug) => (
                    <SelectItem key={drug.drug} value={drug.drug}>
                      {drug.drug === "GLP-1" ? "GLP-1 (General)" : drug.drug} ({drug.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Sort By */}
            <div className="space-y-2">
              <Label htmlFor="sortBy">Sort By</Label>
              <div className="flex gap-2">
                <Select value={sortBy} onValueChange={(value) => setSortBy(value as SortFieldType)}>
                  <SelectTrigger id="sortBy" className="flex-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(SortField).map((field) => (
                      <SelectItem key={field} value={field}>
                        {SORT_FIELD_LABELS[field as SortField]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setSortOrder(sortOrder === SortDirection.ASC ? SortDirection.DESC : SortDirection.ASC)}
                  title={SORT_DIRECTION_TOOLTIPS[sortOrder as SortDirection]}
                  className="shrink-0"
                >
                  <ArrowUpDown className={`h-4 w-4 transition-transform ${sortOrder === SortDirection.ASC ? "rotate-180" : ""}`} />
                </Button>
              </div>
            </div>
          </div>

          {/* Clear Filters - on separate row */}
          <div className="mt-4">
            <Button
              variant="outline"
              onClick={() => {
                setSearchText("")
                setSelectedDrug("all")
                setSortBy(SortField.DATE)
                setSortOrder(SortDirection.DESC)
              }}
            >
              Clear Filters
            </Button>
          </div>

          <div className="mt-4 text-sm text-muted-foreground">
            Showing {experiencesData?.experiences.length ?? 0} of {experiencesData?.total ?? 0} experiences
          </div>
        </Card>

        {/* Experiences Grid */}
        {showSkeleton ? (
          // Loading skeleton for initial load
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="border-border/40 bg-card p-6 animate-pulse">
                <div className="space-y-4">
                  {/* Header skeleton */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="h-6 w-24 bg-muted rounded" />
                      <div className="h-4 w-full bg-muted rounded" />
                      <div className="h-4 w-3/4 bg-muted rounded" />
                    </div>
                    <div className="h-4 w-16 bg-muted rounded" />
                  </div>
                  {/* Stats skeleton */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/40">
                    {Array.from({ length: 4 }).map((_, j) => (
                      <div key={j} className="flex items-center gap-2">
                        <div className="h-4 w-4 bg-muted rounded" />
                        <div className="flex-1 space-y-1">
                          <div className="h-4 w-16 bg-muted rounded" />
                          <div className="h-3 w-12 bg-muted rounded" />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : !experiencesData?.experiences.length ? (
          <Card className="border-border/40 bg-card p-12 text-center">
            <p className="text-muted-foreground">No experiences match your filters</p>
          </Card>
        ) : (
          <div className="relative">
            {/* Show loading overlay when filtering */}
            {isFetching && !isFetchingNextPage && (
              <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
                <div className="flex items-center gap-2 bg-card border border-border px-4 py-2 rounded-lg shadow-lg">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span className="text-sm">Updating results...</span>
                </div>
              </div>
            )}

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {experiencesData.experiences.map((experience, index) => (
                <ExperienceCardComponent
                  key={`${experience.id}-${index}`}
                  experience={experience}
                  onClick={() => setSelectedExperienceId(experience.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Infinite Scroll Trigger */}
        {hasNextPage && (
          <div ref={loadMoreRef} className="mt-8 text-center py-8">
            {isFetchingNextPage ? (
              <div className="flex items-center justify-center gap-2">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="text-muted-foreground">Loading more experiences...</span>
              </div>
            ) : (
              <div className="text-muted-foreground">Scroll to load more</div>
            )}
          </div>
        )}

        {/* End of results */}
        {!hasNextPage && experiencesData.experiences.length > 0 && (
          <div className="mt-8 text-center py-4 text-muted-foreground">
            You've reached the end of the experiences
          </div>
        )}
      </div>

      {/* Experience Detail Dialog */}
      <Dialog open={!!selectedExperienceId} onOpenChange={() => setSelectedExperienceId(null)}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          {selectedExperience && (
            <>
              <DialogHeader>
                <div className="flex items-start justify-between gap-4">
                  <DialogTitle className="text-2xl">User Experience</DialogTitle>
                  {getRedditReference(selectedExperience) && (
                    <RedditLink
                      reference={getRedditReference(selectedExperience)!}
                      showText
                      className="shrink-0"
                    />
                  )}
                </div>
                <DialogDescription>
                  {selectedExperience.primary_drug && (
                    <Badge className="mt-2">{selectedExperience.primary_drug}</Badge>
                  )}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6">
                {/* Summary */}
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Experience</h3>
                  <p className="text-sm leading-relaxed">{selectedExperience.summary}</p>
                </div>

                {/* Key Stats Grid */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {selectedExperience.weightLoss && selectedExperience.weightLossUnit && (
                    <Card className="border-border/40 bg-muted/30 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Weight Loss</div>
                      <div className="text-lg font-bold">
                        {Math.round(selectedExperience.weightLoss)} {selectedExperience.weightLossUnit}
                      </div>
                    </Card>
                  )}

                  {selectedExperience.duration_weeks && (
                    <Card className="border-border/40 bg-muted/30 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Duration</div>
                      <div className="text-lg font-bold">
                        {formatDuration(selectedExperience.duration_weeks)}
                      </div>
                    </Card>
                  )}

                  {selectedExperience.cost_per_month && (
                    <Card className="border-border/40 bg-muted/30 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Monthly Cost</div>
                      <div className="text-lg font-bold">
                        {formatCost(selectedExperience.cost_per_month)}
                      </div>
                    </Card>
                  )}

                  {selectedExperience.recommendation_score !== null && (
                    <Card className="border-border/40 bg-muted/30 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Rating</div>
                      <div className="text-lg font-bold text-primary">
                        {(selectedExperience.recommendation_score * 10).toFixed(1)}/10
                      </div>
                    </Card>
                  )}

                  {selectedExperience.sentiment_post !== null && (
                    <Card className="border-border/40 bg-muted/30 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Satisfaction</div>
                      <div className="text-lg font-bold text-primary">
                        {Math.round(selectedExperience.sentiment_post * 100)}%
                      </div>
                    </Card>
                  )}
                </div>

                {/* Side Effects */}
                {selectedExperience.top_side_effects.length > 0 && (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-muted-foreground">
                      Reported Side Effects
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedExperience.top_side_effects.map((effect: string) => (
                        <Badge key={effect} variant="outline" className="capitalize">
                          {effect}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Demographics */}
                {(selectedExperience.age ||
                  selectedExperience.sex ||
                  selectedExperience.location) && (
                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-muted-foreground">
                      Demographics
                    </h3>
                    <div className="flex flex-wrap gap-4 text-sm">
                      {selectedExperience.age && (
                        <div>
                          <span className="text-muted-foreground">Age:</span>{" "}
                          <span className="font-medium">{selectedExperience.age}</span>
                        </div>
                      )}
                      {selectedExperience.sex && (
                        <div>
                          <span className="text-muted-foreground">Gender:</span>{" "}
                          <span className="font-medium capitalize">{selectedExperience.sex}</span>
                        </div>
                      )}
                      {selectedExperience.location && (
                        <div>
                          <span className="text-muted-foreground">Location:</span>{" "}
                          <span className="font-medium">{selectedExperience.location}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Timestamp */}
                <div className="text-xs text-muted-foreground">
                  Processed: {new Date(selectedExperience.processed_at).toLocaleDateString()}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default ExperiencesPage
