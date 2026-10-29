// The secrets this function reads; loaded from Doppler before it runs.
const DOPPLER_SECRETS = ["INTERNAL_API_KEY"];

const SERVICE_URL = process.env.POST_EXTRACTION_URL
  ? `https://${process.env.POST_EXTRACTION_URL}`
  : "https://post-extraction.railway.internal";
const ENDPOINT = "/api/extract";

const extractPosts = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Post Extraction Trigger");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Target: ${SERVICE_URL}${ENDPOINT}?limit=1000`);
  console.log("=".repeat(80));

  try {
    console.log("📡 Sending request to post-extraction service...");
    console.log(`   Method: POST`);
    console.log(`   Query: limit=1000`);

    // Fail closed: never call a service without a usable key.
    const internalApiKey = process.env.INTERNAL_API_KEY;
    if (!internalApiKey || /\s/.test(internalApiKey)) {
      throw new Error("INTERNAL_API_KEY is missing or contains whitespace; refusing to call the service");
    }

    const response = await fetch(`${SERVICE_URL}${ENDPOINT}?limit=1000`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-internal-api-key": internalApiKey,
      },
      body: JSON.stringify({}),
    });

    console.log(
      `📥 Response Status: ${response.status} ${response.statusText}`
    );
    console.log(
      `   Headers: ${JSON.stringify(Object.fromEntries(response.headers))}`
    );

    if (!response.ok) {
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

// No top-level await: the function runner may wrap this file, so the load runs inside main.
const main = async () => {
  await loadDopplerSecrets(DOPPLER_SECRETS);
  await extractPosts();
};

main();
