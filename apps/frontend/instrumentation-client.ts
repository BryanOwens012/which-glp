import posthog from 'posthog-js';

const POSTHOG_DEFAULTS_DATE = '2026-01-30';

const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;

if (posthogKey) {
  try {
    posthog.init(posthogKey, {
      api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
      ui_host: 'https://us.posthog.com',
      defaults: POSTHOG_DEFAULTS_DATE,
    });
  } catch (e) {
    console.warn('[PostHog] Failed to initialize:', e);
  }
}
