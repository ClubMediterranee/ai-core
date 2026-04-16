---
date: 2026-04-03
task: Refactor auth middleware to use JWT RS256 instead of HS256
mode: feature
agent: claude-sonnet
session-start: 09:14
---

# Diary — Auth Middleware Refactor (JWT RS256)

## Entry — 09:14

### What I did
Read the existing auth middleware at `src/middleware/auth.ts` and the JWT utility at `src/utils/jwt.ts`. Mapped all call sites using Grep.

### Why
Need to understand the full blast radius before touching anything. Found 11 files importing `verifyToken` — more than expected.

### What worked
`Grep` for `verifyToken` across the codebase gave a complete picture in one pass.

### What didn't work
Tried to read `src/config/secrets.ts` first but it only imports from env — no hardcoded keys to migrate.

### What I learned
The current `HS256` secret is loaded via `JWT_SECRET` env var. There are two token types: `access` (15 min) and `refresh` (7 days). They share the same secret, which is part of why the migration to RS256 is needed — different keys per token type become possible.

### What was tricky
Two test files mock `verifyToken` with `jest.mock`. Those mocks will need updating after the refactor, otherwise tests pass against the old interface silently.

### Future work
- Generate RSA key pair (or confirm existing ones in secrets manager)
- Update `verifyToken` and `signToken` in `jwt.ts`
- Update all 11 call sites
- Update Jest mocks in `src/__tests__/auth.test.ts` and `src/__tests__/middleware.test.ts`

### Technical details
- `src/middleware/auth.ts` — main middleware (32 lines)
- `src/utils/jwt.ts` — `signToken`, `verifyToken`, `decodeToken` (58 lines)
- Call sites: 11 files, grep: `import.*verifyToken`
- Current algorithm: `HS256`, target: `RS256`
- Env var: `JWT_SECRET` → will become `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY`

---

## Entry — 09:47

### What I did
Updated `src/utils/jwt.ts`: replaced `HS256` with `RS256`, added PEM key loading, updated `signToken` to accept `privateKey` and `verifyToken` to accept `publicKey`. Kept the existing function signatures backward-compatible via optional parameters while the migration is in progress.

### Why
Keeping backward compatibility means I can migrate call sites incrementally rather than in a single big-bang commit. Reduces risk of breakage.

### What worked
TypeScript's union types let me type the key parameter as `string | { privateKey: string; publicKey: string }` cleanly.

### What didn't work
Initially tried to load keys from env inside `jwt.ts` directly — bad idea because it makes the function impure and harder to test. Reverted to passing keys as parameters.

### What I learned
`jsonwebtoken`'s `verify()` with RS256 requires the full PEM string including headers (`-----BEGIN PUBLIC KEY-----`). Passing just the base64 body causes a cryptic `invalid signature` error with no hint about the format.

### What was tricky
The `refresh` token verification path was buried in `src/routes/auth.ts:refreshToken()`, not in the middleware. Almost missed it.

### Future work
- Update `src/routes/auth.ts:refreshToken()` — needs the public key passed through
- Update remaining 10 call sites
- Run test suite to see current failure count

### Technical details
- Modified: `src/utils/jwt.ts` — added `algorithm: 'RS256'` option, PEM key params
- PEM format required: full header + base64 body + footer
- `jsonwebtoken` version: `9.0.2` (supports RS256 natively)
- New env vars needed: `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY` (PEM strings, newlines as `\n`)

---

## Session Close — 11:23

### Summary
Completed the RS256 migration for `jwt.ts` and 9 of 11 call sites. Two remaining call sites are in `src/routes/auth.ts` (the refresh token path) and `src/integrations/third-party-webhook.ts` (external webhook verification — needs separate public key). All updated Jest mocks are passing. The core middleware is fully migrated and tested.

### What's next
- Migrate `src/routes/auth.ts:refreshToken()` and `src/integrations/third-party-webhook.ts`
- Generate production RSA keys and update secrets manager
- Update `.env.example` with new key format documentation

### Open questions
- Does the third-party webhook use our public key or their own? Need to check the webhook provider docs.
- Should `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` be base64-encoded in the env to avoid newline escaping issues in CI?
