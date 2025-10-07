"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Navigation } from "@/components/navigation";
import { DrugComparison } from "@/components/drug-comparison";
import { ArrowRight, RefreshCw } from "lucide-react";
import { trpc } from "@/lib/trpc";

const ComparePage = () => {
  // Fetch real platform stats from backend
  const { data: stats, isLoading } = trpc.platform.getStats.useQuery();
  return (
    <div className="min-h-screen">
      <Navigation />

      <section className="container mx-auto px-4 pt-32 pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-balance md:text-6xl">
            Which <span className="text-primary">weight-loss drug</span>{" "}
            is right for you?
          </h1>
          <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
            Compare based on real user experiences
          </p>
          <div className="flex justify-center">
            <Badge variant="secondary" className="gap-1.5">
              <RefreshCw className="h-3.5 w-3.5" />
              Updated weekly
            </Badge>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y border-border/40 bg-card/30">
        <div className="container mx-auto px-4 py-8">
          {isLoading ? (
            <div className="text-center text-muted-foreground">
              Loading stats...
            </div>
          ) : stats ? (
            <div className="grid grid-cols-2 gap-4 md:gap-8 max-w-2xl mx-auto">
              <div className="text-center">
                <div className="mb-1 text-3xl font-bold text-primary">
                  {(() => {
                    const count = stats.totalExperiences;
                    if (count < 1000) {
                      // Round to nearest hundred for hundreds (e.g., 842 -> 800)
                      return `${Math.floor(count / 100) * 100}+`;
                    } else {
                      // Round to 2 significant figures for thousands (e.g., 5842 -> 5800)
                      const magnitude = Math.pow(
                        10,
                        Math.floor(Math.log10(count)) - 1
                      );
                      return `${Math.floor(count / magnitude) * magnitude}+`;
                    }
                  })()}
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
                  Weight-Loss Drugs
                </div>
              </div>
            </div>
          ) : null}
          <div className="mt-4 text-center">
            <p className="text-xs text-muted-foreground">
              Data sourced from dozens of popular Reddit communities
            </p>
          </div>
        </div>
      </section>

      <section className="container mx-auto px-4 py-16">
        <DrugComparison />
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
              <Link href="/recommendations">
                Get Personalized Recommendations <ArrowRight className="h-4 w-4" />
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

export default ComparePage;
