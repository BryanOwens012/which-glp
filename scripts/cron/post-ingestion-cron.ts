#!/usr/bin/env node
/**
 * Railway Cron Job - Trigger Post Ingestion
 *
 * This script is run by Railway on a cron schedule to trigger
 * the post-ingestion service via its internal API endpoint.
 *
 * Schedule: Every 2 days at noon UTC (0 12 */2 * *)
 */

const SERVICE_URL = process.env.POST_INGESTION_URL
  ? `https://${process.env.POST_INGESTION_URL}`
  : "http://post-ingestion.railway.internal";
const ENDPOINT = "/api/ingest";

const ingestPosts = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Post Ingestion Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    console.log("📡 Sending request to post-ingestion service...");
    console.log(`   Method: POST`);
    console.log(
      `   Body: ${JSON.stringify({ all_tiers: true, posts_limit: 100 })}`
    );

    // Fail closed: never call a service without a usable key.
    const internalApiKey = process.env.INTERNAL_API_KEY;
    if (!internalApiKey || !/^[\x21-\x7e]+$/.test(internalApiKey)) {
      throw new Error("INTERNAL_API_KEY is missing or is not printable ASCII without whitespace; refusing to call the service");
    }

    const response = await fetch(`${SERVICE_URL}${ENDPOINT}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-internal-api-key": internalApiKey,
      },
      redirect: "error", // never follow a redirect, so the key only goes to the service
      body: JSON.stringify({
        all_tiers: true,
        posts_limit: 100,
      }),
    });

    console.log(`📥 Response Status: ${response.status} ${response.statusText}`);
    console.log(
      `   Headers: ${JSON.stringify(Object.fromEntries(response.headers))}`
    );

    // A 409 means the job is already running: a skip, not a failure.
    if (!response.ok && response.status !== 409) {
      throw new Error(`Service responded ${response.status} ${response.statusText}`);
    }
    const data = await response.json();

    console.log("✅ Request successful!");
    console.log("Response Body:", JSON.stringify(data, null, 2));
    console.log("=".repeat(80));
    console.log("🏁 CRON JOB COMPLETED");
    console.log("=".repeat(80));

    process.exit(0);
  } catch (error) {
    console.error("=".repeat(80));
    console.error("❌ CRON JOB FAILED");
    console.error("Error:", error.message);
    console.error("Stack:", error.stack);
    console.error("=".repeat(80));
    process.exit(1);
  }
};

ingestPosts();
