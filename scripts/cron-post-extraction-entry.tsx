#!/usr/bin/env node
/**
 * Railway Cron Job - Post Extraction Entry Point
 *
 * Direct entry point for the post-extraction cron service.
 * Railway will run this file directly.
 */

console.log("=".repeat(80));
console.log("🚀 Post Extraction Cron - Starting");
console.log(`   Time: ${new Date().toISOString()}`);
console.log("=".repeat(80));

// Import and run the actual trigger script
await import('./cron-trigger-post-extraction.js');
