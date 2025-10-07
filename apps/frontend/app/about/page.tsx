"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { ArrowRight, MapPin, Users, TrendingUp, Sparkles } from "lucide-react";

const AboutPage = () => {
  return (
    <div className="min-h-screen">
      <Navigation />

      <section className="container mx-auto px-4 pt-32 pb-12">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-balance md:text-6xl">
            About <span className="text-primary">WhichGLP</span>
          </h1>
          <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
            Real-world data and insights you won't find anywhere else
          </p>
        </div>
      </section>

      <section className="border-y border-border/40 bg-card/30">
        <div className="container mx-auto px-4 py-16">
          <div className="mb-12 text-center">
            <h2 className="mb-3 text-3xl font-bold">What makes us different</h2>
            <p className="text-lg text-muted-foreground">
              Real-world insights from actual user experiences
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card className="border-border/40 bg-card p-6">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">Community Insights</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Learn from thousands of experiences from popular Reddit
                communities like r/Ozempic, r/Wegovy, and r/Mounjaro
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
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">
                Real-Time Market Data
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Track shortages, price changes, and emerging trends
              </p>
            </Card>
          </div>
        </div>
      </section>

      <section className="border-t border-border/40">
        <div className="container mx-auto px-4 py-16">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mb-3 text-3xl font-bold">
              Get recommendations
            </h2>
            <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
              See recommendations based on your profile, location, and health
              conditions
            </p>
            <Button size="lg" className="gap-2" asChild>
              <Link href="/recommendations">
                Recommend for Me <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default AboutPage;
