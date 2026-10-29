/**
 * Log redaction for Supabase secret keys (`sb_secret_...`).
 *
 * The Python services apply the same rule in
 * `scripts/legacy-ingestion/shared/supabase_key.py`; keep the two in sync.
 */

/** Broader than a valid key on purpose: anything after the prefix is masked. */
const SECRET_KEY_PATTERN = /sb_secret_[A-Za-z0-9_-]*/g

const REDACTED = 'sb_secret_[REDACTED]'

export const redactSupabaseSecrets = (text: string): string =>
  text.replace(SECRET_KEY_PATTERN, REDACTED)

/** Redact strings, and the message and stack of errors; pass anything else through. */
const redactArg = (arg: unknown): unknown => {
  if (typeof arg === 'string') {
    return redactSupabaseSecrets(arg)
  }

  if (arg instanceof Error) {
    const message = redactSupabaseSecrets(arg.message)
    const stack = arg.stack === undefined ? undefined : redactSupabaseSecrets(arg.stack)

    if (message === arg.message && stack === arg.stack) {
      return arg
    }

    const copy = new Error(message)
    copy.name = arg.name
    copy.stack = stack
    return copy
  }

  return arg
}

const CONSOLE_METHODS = ['log', 'info', 'warn', 'error', 'debug'] as const

let isInstalled = false

/**
 * Route every `console` method through the redactor, so no log line from this
 * process (ours or a library's) carries a Supabase secret key. Objects are
 * passed through untouched: redacting them would mean serializing them here.
 * Idempotent.
 */
export const installConsoleRedaction = (): void => {
  if (isInstalled) {
    return
  }

  isInstalled = true

  for (const method of CONSOLE_METHODS) {
    const original = console[method].bind(console)
    console[method] = (...args: unknown[]) => {
      original(...args.map(redactArg))
    }
  }
}
