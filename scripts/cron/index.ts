#!/usr/bin/env node
/**
 * Railway Cron Job Entry Point
 *
 * This is the main entry point that Railway auto-detects for Bun functions.
 * It determines which cron script to run based on environment variable.
 */

const CRON_TYPE = process.env.CRON_TYPE;

console.log("=".repeat(80));
console.log("🚀 Railway Cron Job Entry Point");
console.log(`   CRON_TYPE: ${CRON_TYPE}`);
console.log(`   Time: ${new Date().toISOString()}`);
console.log("=".repeat(80));

async function runCronJob() {
  switch (CRON_TYPE) {
    case 'post-ingestion':
      console.log("📥 Running post-ingestion trigger...");
      await import('./post-ingestion-cron.ts');
      break;

    case 'post-extraction':
      console.log("🔍 Running post-extraction trigger...");
      await import('./post-extraction-cron.ts');
      break;

    case 'user-extraction':
      console.log("👤 Running user-extraction trigger...");
      await import('./user-extraction-cron.ts');
      break;

    case 'view-refresher':
      console.log("🔄 Running view-refresher trigger...");
      await import('./view-refresher-cron.ts');
      break;

    default:
      console.error(`❌ Unknown CRON_TYPE: ${CRON_TYPE}`);
      console.error("   Valid values: post-ingestion, post-extraction, user-extraction, view-refresher");
      process.exit(1);
  }
}

runCronJob().catch((error) => {
  console.error("❌ Cron job failed:");
  console.error(error);
  process.exit(1);
});
