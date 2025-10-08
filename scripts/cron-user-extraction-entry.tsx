#!/usr/bin/env node
/**
 * Railway Cron Job - User Extraction Entry Point
 *
 * Direct entry point for the user-extraction cron service.
 * Railway will run this file directly.
 */

console.log("=".repeat(80));
console.log("🚀 User Extraction Cron - Starting");
console.log(`   Time: ${new Date().toISOString()}`);
console.log("=".repeat(80));

// Import and run the actual trigger script
await import("./cron-trigger-user-extraction.js");
