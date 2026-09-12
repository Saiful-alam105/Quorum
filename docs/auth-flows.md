# Quorum — Auth Flows (Demo Note)

Date: 2026-09-12. From `roadmap.md` §3 and `src/quorum/auth/`.

Two separate concepts (do not conflate):

1. Login / identity — GitHub OAuth ("Who is this user?"):
   - Dashboard → Continue with GitHub → callback → session cookie.
   - Routes: `/auth/login`, `/auth/callback`, `/auth/me`, `/auth/logout`.
   - Persisted as the Quorum user.

2. Repository access — GitHub App installation/authorization
   ("Which repositories can Quorum analyze?"):
   - User installs/authorizes the App and selects repositories.
   - Backend maps installations/repositories to the correct user and
     enforces user-level isolation.
   - Uninstall/revocation handling is implemented in the webhook layer.

Secrets and private keys stay on the backend; the frontend never sees them.
