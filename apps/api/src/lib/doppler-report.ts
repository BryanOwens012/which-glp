/**
 * Startup report of the secrets this service receives from Doppler.
 *
 * Doppler syncs secrets into Railway's production shared variables, and each
 * service references the ones it reads. `.railway/railway.ts` sets
 * DOPPLER_VARIABLE_NAMES on every service to the comma-separated names of those
 * references, so the expected list has one source. Values are never logged.
 *
 * A service cannot tell why a secret is missing (absent from Doppler, a failed
 * sync, a reference to a shared variable that does not exist): it sees only
 * `unset` or `empty`, and the report says which.
 *
 * The Python services keep the same report in
 * `scripts/legacy-ingestion/shared/doppler_report.py`, and the cron functions
 * inline in `.railway/functions/`; keep them in sync.
 */

const EXPECTED_NAMES_VARIABLE = 'DOPPLER_VARIABLE_NAMES'

const failureReasons = ['unset', 'empty'] as const
type FailureReason = (typeof failureReasons)[number]

export type DopplerReport = {
  pulled: string[]
  failed: { name: string; reason: FailureReason }[]
}

/** Compare the expected Doppler secrets against `env`; null when there is no expected list. */
export const buildDopplerReport = (env: Record<string, string | undefined>): DopplerReport | null => {
  const raw = env[EXPECTED_NAMES_VARIABLE]
  if (raw === undefined) {
    return null
  }

  const names = [...new Set(raw.split(',').map((name) => name.trim()).filter((name) => name.length > 0))].sort()
  const report: DopplerReport = { pulled: [], failed: [] }
  for (const name of names) {
    const value = env[name]
    if (value === undefined) {
      report.failed.push({ name, reason: 'unset' })
    } else if (value === '') {
      report.failed.push({ name, reason: 'empty' })
    } else {
      report.pulled.push(name)
    }
  }
  return report
}

/** One log line: counts, then the pulled names, then the failed names with reasons. */
export const formatDopplerReport = (report: DopplerReport): string => {
  const expected = report.pulled.length + report.failed.length
  const failed = report.failed.map(({ name, reason }) => `${name} (${reason})`)
  return `[doppler] pulled ${report.pulled.length} of ${expected} secrets, ${report.failed.length} failed; pulled=${JSON.stringify(report.pulled)} failed=${JSON.stringify(failed)}`
}

/** Log the startup report: console.info when every secret arrived, console.warn when any failed. */
export const logDopplerReport = (env: Record<string, string | undefined> = process.env): DopplerReport | null => {
  const report = buildDopplerReport(env)
  if (report === null) {
    console.info(`[doppler] ${EXPECTED_NAMES_VARIABLE} is not set; skipping the secrets report`)
    return null
  }

  const line = formatDopplerReport(report)
  if (report.failed.length > 0) {
    console.warn(line)
  } else {
    console.info(line)
  }
  return report
}
