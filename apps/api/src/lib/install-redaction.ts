/**
 * Side-effect module: imported first by `index.ts`, so console redaction is in
 * place before any other module's top-level code runs. ESM evaluates imports
 * in order, while a call in `index.ts`'s body would run only after every
 * import had already evaluated.
 */
import { installConsoleRedaction } from './redact.js'

installConsoleRedaction()
