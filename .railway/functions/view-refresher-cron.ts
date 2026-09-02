import pg from "pg";
import Redis from "ioredis";

const REDIS_URL = process.env.REDIS_URL;
const MV_TIMEOUT_MS = parseInt(process.env.MV_TIMEOUT_MS || "300000", 10);

const MATERIALIZED_VIEWS = ["mv_experiences_denormalized"];

/**
 * Build PG client config from environment variables.
 *
 * Uses the Supabase session pooler for direct PostgreSQL access,
 * which avoids the ~8s timeout on the Supabase REST API / RPC.
 */
const buildClientConfig = (): pg.ClientConfig => {
  // Option 1: Full connection string (preferred)
  if (process.env.DATABASE_URL) {
    console.log("   Using DATABASE_URL");
    return {
      connectionString: process.env.DATABASE_URL,
      ssl: { rejectUnauthorized: false },
      connectionTimeoutMillis: 30000,
    };
  }

  // Option 2: Derive from SUPABASE_URL + SUPABASE_DB_PASSWORD (session pooler)
  const supabaseUrl = process.env.SUPABASE_URL;
  const dbPassword = process.env.SUPABASE_DB_PASSWORD;

  if (supabaseUrl && dbPassword) {
    const projectId = new URL(supabaseUrl).hostname.split(".")[0];
    const poolerHost = `aws-1-us-west-1.pooler.supabase.com`;
    console.log(`   Using session pooler: ${poolerHost}:5432`);
    return {
      host: poolerHost,
      port: 5432,
      database: "postgres",
      user: `postgres.${projectId}`,
      password: dbPassword,
      ssl: { rejectUnauthorized: false },
      connectionTimeoutMillis: 30000,
    };
  }

  throw new Error(
    "Set DATABASE_URL or both SUPABASE_URL + SUPABASE_DB_PASSWORD"
  );
};

const refreshCacheAndMaterializedView = async () => {
  console.log("=".repeat(80));
  console.log("🕐 CRON JOB STARTED - Refresh Cache & Materialized View");
  console.log(`   Time: ${new Date().toISOString()}`);
  console.log(`   Timeout: ${MV_TIMEOUT_MS / 1000}s per view`);
  console.log(`   Views: ${MATERIALIZED_VIEWS.join(", ")}`);
  console.log("=".repeat(80));

  let redis: Redis | undefined;
  const clientConfig = buildClientConfig();
  const client = new pg.Client(clientConfig);

  try {
    // Connect to PostgreSQL via session pooler
    console.log("📡 Connecting to PostgreSQL...");
    await client.connect();
    console.log("✅ Connected to PostgreSQL");

    // Set statement timeout for long-running MV refreshes
    await client.query(`SET statement_timeout = ${MV_TIMEOUT_MS}`);
    console.log(`   Statement timeout set to ${MV_TIMEOUT_MS / 1000}s`);

    // Initialize Redis client (optional)
    if (REDIS_URL) {
      console.log("📡 Initializing Redis client...");
      console.log(`   Redis URL: ${REDIS_URL.replace(/:[^:@]+@/, ":***@")}`);

      redis = new Redis(REDIS_URL, {
        retryStrategy: (times) => {
          console.log(`   Retry attempt ${times}/3...`);
          if (times > 3) {
            console.warn(
              "⚠️  Redis connection failed after 3 attempts, giving up"
            );
            return null;
          }
          return Math.min(times * 200, 3000);
        },
        maxRetriesPerRequest: 3,
        family: 0,
        keepAlive: 30000,
        connectTimeout: 10000,
        enableOfflineQueue: true,
        lazyConnect: false,
      });

      redis.on("error", (err) => {
        console.error("Redis error event:", err.message || err);
      });

      redis.on("connect", () => {
        console.log("📡 Redis connection established");
      });

      redis.on("ready", () => {
        console.log("✅ Redis is ready");
      });

      await new Promise((resolve) => setTimeout(resolve, 1000));
    } else {
      console.warn("⚠️  REDIS_URL not set - skipping Redis cache deletion");
    }

    // Refresh materialized views
    let successCount = 0;
    let failCount = 0;

    for (const mvName of MATERIALIZED_VIEWS) {
      console.log(`\n🔄 Refreshing ${mvName}...`);
      const start = Date.now();

      try {
        await client.query(`REFRESH MATERIALIZED VIEW CONCURRENTLY ${mvName}`);
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        console.log(`✅ ${mvName} refreshed in ${elapsed}s (concurrent)`);
        successCount++;
      } catch (concurrentErr) {
        const errMsg =
          concurrentErr instanceof Error
            ? concurrentErr.message
            : String(concurrentErr);

        // CONCURRENTLY requires a unique index — fall back to regular refresh
        if (errMsg.includes("unique index")) {
          console.log(
            `   CONCURRENTLY not supported, trying regular refresh...`
          );
          const start2 = Date.now();
          try {
            await client.query(`REFRESH MATERIALIZED VIEW ${mvName}`);
            const elapsed2 = ((Date.now() - start2) / 1000).toFixed(1);
            console.log(`✅ ${mvName} refreshed in ${elapsed2}s`);
            successCount++;
          } catch (regularErr) {
            const elapsed2 = ((Date.now() - start2) / 1000).toFixed(1);
            console.error(
              `❌ ${mvName} failed after ${elapsed2}s: ${
                regularErr instanceof Error
                  ? regularErr.message
                  : String(regularErr)
              }`
            );
            failCount++;
          }
        } else {
          const elapsed = ((Date.now() - start) / 1000).toFixed(1);
          console.error(`❌ ${mvName} failed after ${elapsed}s: ${errMsg}`);
          failCount++;
        }
      }
    }

    // Delete Redis cache key (if Redis is configured)
    if (redis) {
      console.log("\n🗑️  Deleting Redis key: drugs:all-stats...");
      try {
        const deletedCount = await redis.del("drugs:all-stats");
        console.log(`✅ Redis key deleted! (${deletedCount} key(s) removed)`);
      } catch (redisError) {
        console.error("❌ Failed to delete Redis key:", redisError);
        console.warn("⚠️  Continuing despite Redis error...");
      }
    } else {
      console.log("⏭️  Skipping Redis cache deletion (Redis not configured)");
    }

    console.log("\n" + "=".repeat(80));
    console.log(
      `🏁 CRON JOB COMPLETED - ${successCount} refreshed, ${failCount} failed`
    );
    console.log("=".repeat(80));

    await client.end();
    if (redis) await redis.quit();
    process.exit(failCount > 0 ? 1 : 0);
  } catch (error) {
    console.error("=".repeat(80));
    console.error("❌ CRON JOB FAILED");
    console.error("Error:", (error as Error).message);
    console.error("Stack:", (error as Error).stack);
    console.error("=".repeat(80));

    await client.end().catch(() => {});
    if (redis) await redis.quit().catch(() => {});
    process.exit(1);
  }
};

refreshCacheAndMaterializedView();
