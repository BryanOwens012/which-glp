import { PostHog } from 'posthog-node';

let posthogClient: PostHog | null = null;

export const initPostHog = (): void => {
  const apiKey = process.env.POSTHOG_API_KEY;

  if (!apiKey) {
    console.log('⚠️  PostHog: API key not configured — server-side analytics disabled');
    return;
  }

  posthogClient = new PostHog(apiKey, {
    host: process.env.POSTHOG_HOST ?? 'https://us.i.posthog.com',
  });

  console.log('✅ PostHog: Initialized');
};

export const getPostHog = (): PostHog | null => posthogClient;

export const captureEvent = (
  distinctId: string,
  event: string,
  properties?: Record<string, unknown>,
): void => {
  if (!posthogClient) return;

  posthogClient.capture({
    distinctId,
    event,
    properties,
  });
};

export const shutdownPostHog = async (): Promise<void> => {
  if (!posthogClient) return;

  try {
    await posthogClient.shutdown();
    console.log('✅ PostHog: Shut down');
  } catch (error) {
    console.warn(
      '[PostHog] Shutdown error:',
      error instanceof Error ? error.message : String(error),
    );
  }
};
