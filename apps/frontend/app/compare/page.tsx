"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Navigation } from "@/components/navigation";
import { DrugComparison } from "@/components/drug-comparison";
import {
  ArrowRight,
  RefreshCw,
  Info,
  Users,
  Pill,
  Database,
} from "lucide-react";
import { trpc } from "@/lib/trpc";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const ComparePage = () => {
  // Fetch real platform stats from backend
  const { data: stats, isLoading } = trpc.platform.getStats.useQuery();
  return (
    <div className="min-h-screen">
      <Navigation />

      <section className="container mx-auto px-4 pt-32 pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-balance md:text-6xl">
            Which <span className="text-primary">weight-loss drug</span> is
            right for you?
          </h1>
          <div className="mb-6 flex items-center justify-center gap-2">
            <p className="text-lg leading-relaxed text-muted-foreground">
              Compare based on real user experiences
            </p>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="inline-flex items-center justify-center rounded-full p-1 hover:bg-muted transition-colors">
                  <Info className="h-4 w-4 text-muted-foreground" />
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs p-4" side="bottom">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                      <Users className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">
                        {stats
                          ? (() => {
                              const count = stats.totalExperiences;
                              if (count < 1000) {
                                return `${Math.floor(count / 100) * 100}+`;
                              } else {
                                const magnitude = Math.pow(
                                  10,
                                  Math.floor(Math.log10(count)) - 1
                                );
                                return `${
                                  Math.floor(count / magnitude) * magnitude
                                }+`;
                              }
                            })()
                          : "..."}{" "}
                        Real User Experiences
                      </div>
                      <div className="text-xs text-muted-foreground">
                        From real people sharing their journeys
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                      <Pill className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">
                        {stats?.uniqueDrugs || "..."} Weight-Loss Drugs
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Comprehensive coverage
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-border space-y-2">
                    <div className="flex items-center gap-1.5">
                      <Database className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground text-wrap">
                        Data sourced from r/Wegovy, r/Zepbound, and dozens of
                        other popular subreddits
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <RefreshCw className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        Updated weekly
                      </span>
                    </div>
                  </div>
                </div>
              </TooltipContent>
            </Tooltip>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            <Button
              size="lg"
              onClick={() => {
                document
                  .getElementById("drug-comparison")
                  ?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Compare
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/recommendations">Recommend for Me</Link>
            </Button>
          </div>
        </div>
      </section>

      <section id="drug-comparison" className="container mx-auto px-4 py-16">
        <DrugComparison />
      </section>

      <section className="border-t border-border/40">
        <div className="container mx-auto px-4 py-16">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mb-3 text-3xl font-bold">Get recommendations</h2>
            <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
              Based on your profile, location, and health conditions
            </p>
            <Button size="lg" className="gap-2" asChild>
              <Link href="/recommendations">
                Recommend for Me <ArrowRight className="h-4 w-4" />
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
