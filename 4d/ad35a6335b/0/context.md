# Session Context

## User Prompts

### Prompt 1

Implement the following plan:

# Plan: Enforce RLS + Internal API Key Auth

## Context

WhichGLP has two critical security gaps:
1. **All pipeline endpoints are publicly accessible** — anyone can trigger expensive AI extraction runs, flood the ingestion pipeline, or spam recommendations
2. **No Supabase RLS** — anyone with the anon key can read/write all tables directly via the Supabase REST API, bypassing the tRPC API entirely

This plan adds two protection layers following the `permit-lead...

### Prompt 2

git checkout -b bryan/whi-103-harden-with-rls-and-internal-api-key

### Prompt 3

Go line by line carefully to check your work

### Prompt 4

Problem: even with these fixes, I'm able to call the post-extraction without sending an internal api key in the hader

### Prompt 5

What I mean is, INTERNAL_API_KEY is set in the API, but the external caller doesn't send a x-internal-api-key

### Prompt 6

Yes, I already did that

### Prompt 7

It has been deployed

### Prompt 8

It's 200. No auth warning

