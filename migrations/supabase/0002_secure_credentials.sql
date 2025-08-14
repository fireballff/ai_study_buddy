-- secure storage for OAuth refresh tokens
create extension if not exists "pgcrypto";

create table if not exists public.secure_credentials (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null,
    provider text not null check (provider = 'google'),
    refresh_token_cipher bytea not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (owner_user_id, provider)
);

create trigger set_secure_credentials_updated_at
    before update on public.secure_credentials
    for each row execute function public.set_updated_at();

alter table public.secure_credentials enable row level security;

create policy "owner-is-user" on public.secure_credentials
    for all using (owner_user_id = auth.uid())
    with check (owner_user_id = auth.uid());
