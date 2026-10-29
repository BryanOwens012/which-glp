// Doppler secrets report at start: how many of this function's Doppler secrets arrived,
// with both name lists and never a value. Keep in sync with apps/api/src/lib/doppler-report.ts.
{
  const expected = process.env.DOPPLER_VARIABLE_NAMES;
  if (expected === undefined) {
    console.log("[doppler] DOPPLER_VARIABLE_NAMES is not set; skipping the secrets report");
  } else {
    const names = [...new Set(expected.split(",").map((name) => name.trim()).filter(Boolean))].sort();
    const pulled = names.filter((name) => process.env[name]);
    const failed = names
      .filter((name) => !process.env[name])
      .map((name) => `${name} (${process.env[name] === undefined ? "unset" : "empty"})`);
    const line = `[doppler] pulled ${pulled.length} of ${names.length} secrets, ${failed.length} failed; pulled=${JSON.stringify(pulled)} failed=${JSON.stringify(failed)}`;
    (failed.length > 0 ? console.warn : console.log)(line);
  }
}

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

    const response = await fetch(`${SERVICE_URL}${ENDPOINT}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-internal-api-key": process.env.INTERNAL_API_KEY ?? "",
      },
      body: JSON.stringify({
        tier1: true,
        tier2: true,
        posts_limit: 100,
      }),
    });

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

ingestPosts();
