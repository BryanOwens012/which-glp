#!/usr/bin/env node
/**
 * Railway Cron Job Entry Point
 *
 * This is the main entry point that Railway auto-detects.
 * It determines which cron script to run based on environment variable.
 */

const CRON_TYPE = process.env.CRON_TYPE;

console.log("=".repeat(80));
console.log("🚀 Railway Cron Job Entry Point");
console.log(`   CRON_TYPE: ${CRON_TYPE}`);
console.log(`   Time: ${new Date().toISOString()}`);
console.log("=".repeat(80));

switch (CRON_TYPE) {
  case 'post-ingestion':
    console.log("📥 Running post-ingestion trigger...");
    await import('./cron-trigger-post-ingestion.js');
    break;

  case 'post-extraction':
    console.log("🔍 Running post-extraction trigger...");
    await import('./cron-trigger-post-extraction.js');
    break;

  case 'user-extraction':
    console.log("👤 Running user-extraction trigger...");
    await import('./cron-trigger-user-extraction.js');
    break;

  default:
    console.error(`❌ Unknown CRON_TYPE: ${CRON_TYPE}`);
    console.error("   Valid values: post-ingestion, post-extraction, user-extraction");
    process.exit(1);
}
