import { createClient } from "@supabase/supabase-js";
import Redis from "ioredis";

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY!;
const REDIS_URL = process.env.REDIS_URL;

const refreshCacheAndMaterializedView = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Refresh Cache & Materialized View");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log("=".repeat(80));

  let supabase;
  let redis;

  try {
    // Initialize Supabase client
    console.log("📡 Initializing Supabase client...");
    supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

    // Initialize Redis client (optional)
    if (REDIS_URL) {
      console.log("📡 Initializing Redis client...");
      console.log(`   Redis URL: ${REDIS_URL.replace(/:[^:@]+@/, ":***@")}`); // Hide password

      redis = new Redis(REDIS_URL, {
        retryStrategy: (times) => {
          console.log(`   Retry attempt ${times}/3...`);
          // Stop retrying after 3 attempts
          if (times > 3) {
            console.warn(
              "⚠️  Redis connection failed after 3 attempts, giving up"
            );
            return null;
          }
          // Exponential backoff, max 3 seconds
          return Math.min(times * 200, 3000);
        },
        maxRetriesPerRequest: 3,
        // Railway IPv6 support - enable dual-stack DNS resolution
        // https://docs.railway.com/reference/errors/enotfound-redis-railway-internal
        family: 0,
        // Reduce keepAlive for Railway's timeout settings
        keepAlive: 30000,
        // Don't wait too long for connections
        connectTimeout: 10000,
        // Enable offline queue to buffer commands while connecting
        enableOfflineQueue: true,
        // Connect immediately (not lazy)
        lazyConnect: false,
      });

      // Add error handler to prevent unhandled error events
      redis.on("error", (err) => {
        console.error("Redis error event:", err.message || err);
      });

      redis.on("connect", () => {
        console.log("📡 Redis connection established");
      });

      redis.on("ready", () => {
        console.log("✅ Redis is ready");
      });

      // Wait a moment for connection to establish
      await new Promise((resolve) => setTimeout(resolve, 1000));
    } else {
      console.warn("⚠️  REDIS_URL not set - skipping Redis cache deletion");
    }

    // Refresh materialized view using RPC function
    console.log(
      "🔄 Refreshing materialized view: mv_experiences_denormalized..."
    );
    const { error: refreshError } = await supabase.rpc(
      "refresh_materialized_view_function",
      {
        view_name: "mv_experiences_denormalized",
      }
    );

    if (refreshError) {
      throw new Error(
        `Failed to refresh materialized view: ${refreshError.message}`
      );
    }

    console.log("✅ Materialized view refreshed successfully!");

    // Delete Redis cache key (if Redis is configured)
    if (redis) {
      console.log("🗑️  Deleting Redis key: drugs:all-stats...");
      try {
        const deletedCount = await redis.del("drugs:all-stats");
        console.log(`✅ Redis key deleted! (${deletedCount} key(s) removed)`);
      } catch (redisError) {
        console.error("❌ Failed to delete Redis key:", redisError);
        // Don't fail the whole job if Redis deletion fails
        console.warn("⚠️  Continuing despite Redis error...");
      }
    } else {
      console.log("⏭️  Skipping Redis cache deletion (Redis not configured)");
    }

    console.log("=".repeat(80));
    console.log("🏁 CRON JOB COMPLETED");
    console.log("=".repeat(80));

    process.exit(0);
  } catch (error) {
    console.error("=".repeat(80));
    console.error("❌ CRON JOB FAILED");
    console.error("Error:", (error as Error).message);
    console.error("Stack:", (error as Error).stack);
    console.error("=".repeat(80));
    process.exit(1);
  } finally {
    // Clean up Redis connection
    if (redis) {
      await redis.quit();
    }
  }
};

refreshCacheAndMaterializedView();
