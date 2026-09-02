import { describe, expect, it } from 'vitest'
import { isHealthRequest, isTrpcRequest } from './routing.js'

describe('isTrpcRequest', () => {
  it('matches the endpoint and its procedure paths', () => {
    expect(isTrpcRequest('/trpc')).toBe(true)
    expect(isTrpcRequest('/trpc/')).toBe(true)
    expect(isTrpcRequest('/trpc/drugs.getAllStats')).toBe(true)
    expect(isTrpcRequest('/trpc/drugs.getAllStats?input=%7B%7D')).toBe(true)
  })

  it('refuses a path that merely starts with the same characters', () => {
    // A bare prefix test would accept these, letting a scanner buy the generous
    // API budget instead of the tight unknown-path budget.
    expect(isTrpcRequest('/trpcwp-login.php')).toBe(false)
    expect(isTrpcRequest('/trpc-admin')).toBe(false)
    expect(isTrpcRequest('/trpcalfa.php')).toBe(false)
  })

  it('refuses unrelated and empty paths', () => {
    expect(isTrpcRequest('/wp-login.php')).toBe(false)
    expect(isTrpcRequest('/')).toBe(false)
    expect(isTrpcRequest(undefined)).toBe(false)
  })
})

describe('isHealthRequest', () => {
  it('matches the health endpoint with or without a trailing slash', () => {
    expect(isHealthRequest('/health')).toBe(true)
    expect(isHealthRequest('/health/')).toBe(true)
    expect(isHealthRequest('/health?verbose=1')).toBe(true)
  })

  it('refuses lookalikes', () => {
    expect(isHealthRequest('/healthcheck.php')).toBe(false)
    expect(isHealthRequest('/health/../wp-login.php')).toBe(false)
    expect(isHealthRequest(undefined)).toBe(false)
  })
})
