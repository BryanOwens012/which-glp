/**
 * Path classification for the HTTP edge.
 *
 * Which budget a request draws on depends on whether it addresses a route this
 * service actually serves, so these predicates are security-relevant: a match
 * that is looser than intended is a way to buy the wrong budget.
 */

/**
 * Whether a URL addresses the tRPC endpoint.
 *
 * Matched on the whole path segment rather than as a bare prefix: a prefix test
 * also accepts `/trpcwp-login.php`, which would let a scanner draw on the
 * generous API budget instead of the tight unknown-path one simply by prefixing
 * its probes.
 */
export const isTrpcRequest = (url: string | undefined): boolean => {
  if (!url) {
    return false
  }

  const path = url.split('?')[0]

  return path === '/trpc' || path.startsWith('/trpc/')
}

/** Whether a URL addresses the health endpoint. */
export const isHealthRequest = (url: string | undefined): boolean => {
  if (!url) {
    return false
  }

  const path = url.split('?')[0]

  return path === '/health' || path === '/health/'
}
