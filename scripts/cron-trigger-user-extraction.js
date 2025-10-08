#!/usr/bin/env node
/**
 * Railway Cron Job - Trigger User Extraction
 *
 * Schedule: Every 2 days at noon UTC (0 12 */2 * *)
 */

import { execSync } from "child_process";

const SERVICE_URL = process.env.USER_EXTRACTION_URL || "https://user-extraction.railway.internal";
const ENDPOINT = "/api/analyze";

const analyzeUsers = () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - User Extraction Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    const command = `curl -X POST ${SERVICE_URL}${ENDPOINT} -H "Content-Type: application/json"`;

    console.log("📡 Sending request to user-extraction service...");
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

analyzeUsers();
