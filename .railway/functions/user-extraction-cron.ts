// The secrets this function reads; loaded from Doppler before it runs.
const DOPPLER_SECRETS = ["INTERNAL_API_KEY"];

const SERVICE_URL = process.env.USER_EXTRACTION_URL
  ? `https://${process.env.USER_EXTRACTION_URL}`
  : "https://user-extraction.railway.internal";
const ENDPOINT = "/api/analyze";

const analyzeUsers = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - User Extraction Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}`);
  console.log("=".repeat(80));

  try {
    console.log("📡 Sending request to user-extraction service...");
    console.log(`   Method: POST`);
    console.log(
      `   Body: ${JSON.stringify({ limit: 10, rate_limit_delay: 2.0 })}`
    );

    const response = await callInternalService(`${SERVICE_URL}${ENDPOINT}`, {
      limit: 100,
      rate_limit_delay: 2.0,
    });

    if (response.status === 409) {
      console.log("⏭️  The service is already running this job; skipping until the next schedule.");
      process.exit(0);
      return;
    }

    console.log(
      `📥 Response Status: ${response.status} ${response.statusText}`
    );
    console.log(
      `   Headers: ${JSON.stringify(Object.fromEntries(response.headers))}`
    );

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

// No top-level await: the function runner may wrap this file, so the load runs inside main.
const main = async () => {
  await loadDopplerSecrets(DOPPLER_SECRETS);
  await analyzeUsers();
};

main();
