"use client"

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Navigation } from "@/components/navigation";
import { DrugComparison } from "@/components/drug-comparison";
import { ArrowRight, MapPin, Users, TrendingUp, Sparkles } from "lucide-react";
import { trpc } from "@/lib/trpc";

const HomePage = () => {
  // Fetch real platform stats from backend
  const { data: stats, isLoading } = trpc.platform.getStats.useQuery();
  return (
    <div className="min-h-screen">
      <Navigation />

      <section className="container mx-auto px-4 pt-32 pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-balance md:text-6xl">
            Compare <span className="text-primary">GLP-1 medications</span>{" "}
            using real-world data
          </h1>
          <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
            Make informed decisions with insights from thousands of user
            experiences
          </p>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y border-border/40 bg-card/30">
        <div className="container mx-auto px-4 py-8">
          {isLoading ? (
            <div className="text-center text-muted-foreground">Loading stats...</div>
          ) : stats ? (
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <div className="text-center">
                <div className="mb-1 text-3xl font-bold text-primary">
                  {stats.totalExperiences.toLocaleString()}+
                </div>
                <div className="text-sm text-muted-foreground">
                  Real User Experiences
                </div>
              </div>
              <div className="text-center">
                <div className="mb-1 text-3xl font-bold text-primary">
                  {stats.uniqueDrugs}
                </div>
                <div className="text-sm text-muted-foreground">
                  GLP-1 Medications
                </div>
              </div>
              <div className="text-center">
                <div className="mb-1 text-3xl font-bold text-primary">
                  {stats.locationsTracked}
                </div>
                <div className="text-sm text-muted-foreground">
                  States Tracked
                </div>
              </div>
              <div className="text-center">
                <div className="mb-1 text-3xl font-bold text-primary">
                  {Math.round(stats.avgWeightLossPercentage)}%
                </div>
                <div className="text-sm text-muted-foreground">
                  Avg. Weight Loss
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="container mx-auto px-4 py-16">
        <DrugComparison />
      </section>

      <section className="border-t border-border/40 bg-card/30">
        <div className="container mx-auto px-4 py-16">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold">Data LLMs don't have</h2>
            <p className="text-lg text-muted-foreground">
              Real-world insights no generic AI can provide
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border/40 bg-card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <MapPin className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">
                Location Intelligence
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Pricing and availability specific to your city and insurance
              </p>
            </Card>

            <Card className="border-border/40 bg-card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">
                Personalized Predictions
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Outcome predictions based on your profile and health factors
              </p>
            </Card>

            <Card className="border-border/40 bg-card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">
                Real-Time Market Data
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Track shortages, price changes, and emerging trends
              </p>
            </Card>

            <Card className="border-border/40 bg-card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">Community Insights</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Learn from thousands of experiences on Reddit and Twitter
              </p>
            </Card>
          </div>
        </div>
      </section>

      <section className="border-t border-border/40">
        <div className="container mx-auto px-4 py-16">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mb-3 text-3xl font-bold">
              Get personalized recommendations
            </h2>
            <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
              See predictions based on your profile, location, and health
              conditions
            </p>
            <Button size="lg" className="gap-2" asChild>
              <Link href="/dashboard">
                View Data Dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="text-sm text-muted-foreground">
              © 2025 WhichGLP. All rights reserved.
            </div>
            <div className="flex gap-6">
              <Link
                href="/privacy"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Privacy
              </Link>
              <Link
                href="/terms"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Terms
              </Link>
              <Link
                href="/contact"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Contact
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
