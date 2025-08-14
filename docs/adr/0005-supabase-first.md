# ADR 0005: Supabase-first Architecture with Local SQLite Cache

## Status

Accepted

## Context

The application originally persisted all data in a local SQLite database and
used ad-hoc sync with Google Calendar. To support multi-device access and
reliable offline behavior, a cloud source of truth was required.

## Decision

- Supabase (Postgres) is the primary store. Row Level Security enforces
  per-user isolation with `owner_user_id = auth.uid()`.
- A local SQLite database mirrors remote state and queues mutations while
  offline. Writes go to Supabase when online and are flagged `dirty` when
  queued locally.
- A background `SyncEngine` drains the `pending_ops` queue and reconciles
  changes using last-writer-wins semantics.

## Consequences

- Users can continue working offline; updates are pushed when connectivity
  returns.
- Conflict resolution is simplified to last-writer-wins based on server
  `updated_at` timestamps and a `version` UUID.
- Additional complexity exists in the repository layer and migrations to
  support mirrored schemas.
