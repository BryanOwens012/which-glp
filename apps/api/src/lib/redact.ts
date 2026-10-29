/**
 * Log redaction for secrets: Supabase secret keys (`sb_secret_...`) and Doppler
 * tokens (`dp.st.…` and the other `dp.*` formats).
 *
 * The Python services apply the same rule in
 * `scripts/legacy-ingestion/shared/supabase_key.py`; keep the two in sync.
 */

/**
 * A superset of what `parseSupabaseSecretKey` accepts (`sb_secret_` plus any
 * non-whitespace), so every accepted key is masked in full.
 */
const SECRET_KEY_PATTERN = /sb_secret_\S*/g

const REDACTED = 'sb_secret_[REDACTED]'

/** Doppler tokens: service (st), CLI (ct), personal (pt), service account (sa), SCIM and audit. */
const DOPPLER_TOKEN_PATTERN = /dp\.(?:st|ct|pt|sa|scim|audit)\.\S+/g

const DOPPLER_REDACTED = 'dp.[REDACTED]'

/** Mask every Supabase secret key and Doppler token in `text`. */
export const redactSecrets = (text: string): string =>
  text.replace(SECRET_KEY_PATTERN, REDACTED).replace(DOPPLER_TOKEN_PATTERN, DOPPLER_REDACTED)

/**
 * Copy an error with secrets masked in its message, stack, string-valued
 * own fields (e.g. a PostgrestError's `details`), and `cause`. The copy keeps
 * the original's prototype, so its class and `instanceof` still hold. `copies`
 * maps each original to its copy, so a self-referencing `cause` chain points at
 * the masked copy instead of recursing forever or leaking the original.
 */
const redactError = (error: Error, copies: Map<Error, Error>): Error => {
  const existing = copies.get(error)
  if (existing) {
    return existing
  }

  const copy: Error = Object.create(Object.getPrototypeOf(error))
  copies.set(error, copy)

  for (const key of Object.getOwnPropertyNames(error)) {
    const value: unknown = Reflect.get(error, key)
    Object.defineProperty(copy, key, {
      value: redactArg(value, copies),
      writable: true,
      enumerable: Object.prototype.propertyIsEnumerable.call(error, key),
      configurable: true,
    })
  }

  return copy
}

/**
 * Redact strings, errors, and arrays of them (an `AggregateError`'s `errors`);
 * pass anything else (plain objects included) through.
 */
const redactArg = (arg: unknown, copies: Map<Error, Error> = new Map()): unknown => {
  if (typeof arg === 'string') {
    return redactSecrets(arg)
  }

  if (arg instanceof Error) {
    return redactError(arg, copies)
  }

  if (Array.isArray(arg)) {
    return arg.map((item) => redactArg(item, copies))
  }

  return arg
}

const CONSOLE_METHODS = ['log', 'info', 'warn', 'error', 'debug'] as const

type ConsoleMethod = (typeof CONSOLE_METHODS)[number]

type ConsoleLike = Pick<Console, ConsoleMethod>

const installedTargets = new WeakSet<ConsoleLike>()

/**
 * Route each `console` method through the redactor, so no log line from this
 * process (ours or a library's) carries a Supabase secret key or Doppler token. Objects are
 * passed through untouched: redacting them would mean serializing them here.
 * Idempotent per target.
 */
export const installConsoleRedaction = (target: ConsoleLike = console): void => {
  if (installedTargets.has(target)) {
    return
  }

  installedTargets.add(target)

  for (const method of CONSOLE_METHODS) {
    const original = target[method].bind(target)
    target[method] = (...args: unknown[]) => {
      original(...args.map((arg) => redactArg(arg)))
    }
  }
}
