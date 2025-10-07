import Redis from "ioredis";

/**
 * Redis client for caching API responses
 *
 * Configuration:
 * - REDIS_URL: Full Redis connection URL (e.g., redis://localhost:6379)
 * - Falls back to localhost:6379 if not set (for local development)
 *
 * Connection handling:
 * - Lazy connection: connects on first use
 * - Graceful degradation: if Redis is unavailable, cache operations are skipped
 * - Error handling: logs errors but doesn't crash the app
 */

let redisClient: Redis | null = null;
let redisAvailable = true;

/**
 * Get or create the Redis client instance
 * Lazy initialization - only connects when first used
 */
function getRedisClient(): Redis | null {
  if (!redisAvailable) {
    return null;
  }

  if (!redisClient) {
    try {
      const redisUrl = process.env.REDIS_URL || "redis://localhost:6379";
      console.log("🔌 Redis: Initializing connection");

      redisClient = new Redis(redisUrl, {
        // Connection settings
        maxRetriesPerRequest: 3,
        retryStrategy: (times) => {
          // Retry with exponential backoff, max 3 seconds
          if (times > 3) {
            console.error("❌ Redis: Max retries reached, disabling cache");
            redisAvailable = false;
            return null;
          }
          console.log(`🔄 Redis: Retry attempt ${times}/3`);
          return Math.min(times * 200, 3000);
        },
        // Reduce keepAlive for Railway's timeout settings
        keepAlive: 30000,
        // Don't wait too long for connections
        connectTimeout: 10000,
        // Enable offline queue to buffer commands while connecting
        enableOfflineQueue: true,
        // Automatically connect (not lazy)
        lazyConnect: false,
      });

      // Connection event handlers
      redisClient.on("connect", () => {
        console.log("✅ Redis: Connected");
        redisAvailable = true;
      });

      redisClient.on("ready", () => {
        console.log("✅ Redis: Ready to accept commands");
      });

      redisClient.on("error", (err) => {
        console.error("❌ Redis error:", err.message);
        // Don't disable on every error, only on critical ones
        if (
          err.message.includes("ECONNREFUSED") ||
          err.message.includes("ETIMEDOUT")
        ) {
          redisAvailable = false;
        }
      });

      redisClient.on("close", () => {
        console.log("⚠️  Redis: Connection closed");
      });

      redisClient.on("reconnecting", () => {
        console.log("🔄 Redis: Reconnecting...");
      });
    } catch (err) {
      console.error("❌ Redis: Initialization failed:", err);
      redisAvailable = false;
      return null;
    }
  }

  return redisClient;
}

/**
 * Cache wrapper for API responses
 *
 * @param key - Cache key (should be unique per query/params)
 * @param ttl - Time to live in seconds (default: 5 minutes)
 * @param fn - Async function to execute if cache miss
 * @returns Cached value or result of fn()
 *
 * Usage:
 * ```ts
 * const data = await withCache('drugs:all', 300, async () => {
 *   return await fetchFromDatabase()
 * })
 * ```
 */
export async function withCache<T>(
  key: string,
  ttl: number,
  fn: () => Promise<T>
): Promise<T> {
  const client = getRedisClient();

  // If Redis client couldn't be created, skip caching
  if (!client) {
    console.log(`⚠️  Redis client unavailable, skipping cache for key: ${key}`);
    return await fn();
  }

  try {
    // Try to get from cache
    console.log(`🔍 Redis: Attempting GET for key: ${key}`);
    const cached = await client.get(key);

    if (cached) {
      console.log(`✅ Cache HIT: ${key}`);
      return JSON.parse(cached) as T;
    }

    console.log(`⚠️  Cache MISS: ${key}`);

    // Cache miss - execute function
    const result = await fn();

    // Store in cache (fire and forget, don't wait)
    console.log(`💾 Redis: Setting cache for key: ${key} (TTL: ${ttl}s)`);
    client.setex(key, ttl, JSON.stringify(result)).catch((err) => {
      console.error(`❌ Redis: Failed to set cache for ${key}:`, err.message);
    });

    return result;
  } catch (err) {
    // If any Redis operation fails, fall back to executing the function
    console.error(`❌ Redis operation failed for ${key}:`, err);
    return await fn();
  }
}

/**
 * Manually invalidate a cache key or pattern
 *
 * @param pattern - Key or pattern to delete (e.g., "drugs:*" to delete all drug-related keys)
 */
export async function invalidateCache(pattern: string): Promise<void> {
  const client = getRedisClient();

  if (!client || !redisAvailable) {
    console.log(`⚠️  Redis unavailable, cannot invalidate: ${pattern}`);
    return;
  }

  try {
    if (pattern.includes("*")) {
      // Pattern-based deletion using SCAN (non-blocking)
      const keys: string[] = [];
      let cursor = "0";

      do {
        const result = await client.scan(
          cursor,
          "MATCH",
          pattern,
          "COUNT",
          100
        );
        cursor = result[0];
        keys.push(...result[1]);
      } while (cursor !== "0");

      if (keys.length > 0) {
        await client.del(...keys);
        console.log(`✅ Invalidated ${keys.length} keys matching: ${pattern}`);
      } else {
        console.log(`⚠️  No keys found matching: ${pattern}`);
      }
    } else {
      // Single key deletion
      await client.del(pattern);
      console.log(`✅ Invalidated cache: ${pattern}`);
    }
  } catch (err) {
    console.error(`❌ Failed to invalidate cache ${pattern}:`, err);
  }
}

/**
 * Get cache statistics (hits, misses, size)
 * Useful for monitoring and debugging
 */
export async function getCacheStats(): Promise<{
  available: boolean;
  connectedClients?: number;
  usedMemory?: string;
  keys?: number;
} | null> {
  const client = getRedisClient();

  if (!client || !redisAvailable) {
    return { available: false };
  }

  try {
    const info = await client.info("stats");
    const dbSize = await client.dbsize();

    return {
      available: true,
      keys: dbSize,
      connectedClients: parseInt(
        info.match(/connected_clients:(\d+)/)?.[1] || "0"
      ),
      usedMemory: info.match(/used_memory_human:([^\r\n]+)/)?.[1] || "unknown",
    };
  } catch (err) {
    console.error("❌ Failed to get cache stats:", err);
    return null;
  }
}

/**
 * Gracefully close Redis connection
 * Should be called on server shutdown
 */
export async function closeRedis(): Promise<void> {
  if (redisClient) {
    try {
      await redisClient.quit();
      console.log("✅ Redis: Connection closed gracefully");
    } catch (err) {
      console.error("❌ Redis: Error during shutdown:", err);
    }
  }
}
