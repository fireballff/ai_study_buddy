-- Supabase schema for AI Study Buddy
-- Run via Supabase SQL editor or migration tooling

-- Extensions
create extension if not exists "pgcrypto";
create extension if not exists "uuid-ossp";

-- tasks table
create table if not exists public.tasks (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    version uuid not null default gen_random_uuid(),
    source text not null,
    source_id text not null,
    title text not null,
    type text not null,
    estimated_duration integer not null default 0,
    due_date timestamptz,
    state text not null default 'pending',
    start_time timestamptz,
    end_time timestamptz,
    course_label text,
    priority int not null default 0,
    unique (owner_user_id, source, source_id)
);
create index if not exists tasks_owner_state_due_idx on public.tasks(owner_user_id, state, due_date);

-- events table
create table if not exists public.events (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    version uuid not null default gen_random_uuid(),
    source text not null,
    source_id text not null,
    title text not null,
    start_time timestamptz not null,
    end_time timestamptz not null,
    type text not null,
    description text not null default '',
    etag text,
    calendar_id text,
    unique (owner_user_id, source, source_id)
);
create index if not exists events_owner_time_idx on public.events(owner_user_id, start_time, end_time);

-- planner preferences (one row per user)
create table if not exists public.planner_prefs (
    owner_user_id uuid primary key,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    focus_block_minutes int default 50,
    break_minutes int default 10,
    adhd_mode_enabled boolean default false,
    deleted_at timestamptz,
    version uuid not null default gen_random_uuid()
);

-- user hard blocks
create table if not exists public.blocks (
    id uuid primary key default gen_random_uuid(),
    owner_user_id uuid not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    version uuid not null default gen_random_uuid(),
    title text not null,
    start_time timestamptz not null,
    end_time timestamptz not null
);
create index if not exists blocks_owner_time_idx on public.blocks(owner_user_id, start_time, end_time);

-- sync state
create table if not exists public.sync_state (
    owner_user_id uuid not null,
    provider text not null,
    cursor text,
    last_full_sync timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    version uuid not null default gen_random_uuid(),
    primary key (owner_user_id, provider)
);

-- app meta
create table if not exists public.app_meta (
    key text primary key,
    value text not null
);

-- updated_at trigger
create or replace function public.set_updated_at() returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger set_tasks_updated_at before update on public.tasks
    for each row execute function public.set_updated_at();
create trigger set_events_updated_at before update on public.events
    for each row execute function public.set_updated_at();
create trigger set_blocks_updated_at before update on public.blocks
    for each row execute function public.set_updated_at();
create trigger set_planner_prefs_updated_at before update on public.planner_prefs
    for each row execute function public.set_updated_at();
create trigger set_sync_state_updated_at before update on public.sync_state
    for each row execute function public.set_updated_at();

-- RLS policies
do $$
begin
    for t in select tablename from pg_tables where schemaname = 'public' loop
        execute format('alter table public.%I enable row level security', t.tablename);
    end loop;
end$$;

create policy "owner-is-user" on public.tasks for all using (owner_user_id = auth.uid());
create policy "owner-is-user" on public.events for all using (owner_user_id = auth.uid());
create policy "owner-is-user" on public.planner_prefs for all using (owner_user_id = auth.uid());
create policy "owner-is-user" on public.blocks for all using (owner_user_id = auth.uid());
create policy "owner-is-user" on public.sync_state for all using (owner_user_id = auth.uid());
