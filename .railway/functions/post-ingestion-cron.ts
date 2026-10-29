// The secrets this function reads; loaded from Doppler before it runs.
const DOPPLER_SECRETS = ["INTERNAL_API_KEY"];

console.log("Starting now");

const SERVICE_URL = process.env.POST_INGESTION_URL
  ? `https://${process.env.POST_INGESTION_URL}`
  : "https://post-ingestion.railway.internal";
const ENDPOINT = "/api/ingest";

const ingestPosts = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Post Ingestion Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    console.log("📡 Sending request to post-ingestion service...");

    const response = await callInternalService(`${SERVICE_URL}${ENDPOINT}`, {
      tier1: true,
      tier2: true,
      posts_limit: 100,
    });

    if (response.status === 409) {
      console.log("⏭️  The service is already running this job; skipping until the next schedule.");
      process.exit(0);
      return;
    }

    const data = await response.json();

    console.log("✅ Request successful!");
    console.log("Response:", JSON.stringify(data, null, 2));
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

// No top-level await: the function runner may wrap this file, so the load runs inside main.
const main = async () => {
  await loadDopplerSecrets(DOPPLER_SECRETS);
  await ingestPosts();
};

// A failed Doppler load throws before the job's own try/catch; fail the run either way.
main().catch((error) => {
  console.error("❌ CRON JOB FAILED:", error instanceof Error ? error.message : error);
  process.exit(1);
});
