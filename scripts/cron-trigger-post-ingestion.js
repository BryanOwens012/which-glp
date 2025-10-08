#!/usr/bin/env node
/**
 * Railway Cron Job - Trigger Post Ingestion
 *
 * This script is run by Railway on a cron schedule to trigger
 * the post-ingestion service via its internal API endpoint.
 *
 * Schedule: Every 2 days at noon UTC (0 12 */2 * *)
 */

import { execSync } from "child_process";

const SERVICE_URL = process.env.POST_INGESTION_URL || "https://post-ingestion.railway.internal";
const ENDPOINT = "/api/ingest";

const ingestPosts = () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Post Ingestion Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    const command = `curl -X POST ${SERVICE_URL}${ENDPOINT} -H "Content-Type: application/json" -d '{"all_tiers": true, "posts_limit": 100}'`;

    console.log("📡 Sending request to post-ingestion service...");
    const output = execSync(command, { encoding: 'utf-8' });

    console.log("✅ Request successful!");
    console.log("Response:", output);
    console.log("=".repeat(80));
    console.log("🏁 CRON JOB COMPLETED");
    console.log("=".repeat(80));

    process.exit(0);
  } catch (error) {
    console.error("=".repeat(80));
    console.error("❌ CRON JOB FAILED");
    console.error("Error:", error.message);
    console.error("=".repeat(80));
    process.exit(1);
  }
};

ingestPosts();
