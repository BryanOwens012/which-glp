#!/usr/bin/env node
/**
 * Railway Cron Job - Trigger Post Extraction
 *
 * Schedule: Every 2 days at noon UTC (0 12 */2 * *)
 */

import { execSync } from "child_process";

const SERVICE_URL = process.env.POST_EXTRACTION_URL || "https://post-extraction.railway.internal";
const ENDPOINT = "/api/extract";

const extractPosts = () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Post Extraction Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    const command = `curl -X POST "${SERVICE_URL}${ENDPOINT}?limit=2000" -H "Content-Type: application/json"`;

    console.log("📡 Sending request to post-extraction service...");
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

extractPosts();
