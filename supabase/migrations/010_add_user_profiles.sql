-- 010_add_user_profiles.sql

-- 1. Create the user_profiles table
create table public.user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    full_name text,
    has_completed_onboarding boolean default false not null
);
comment on table public.user_profiles is 'Stores public-facing profile data for each user.';

-- 2. Enable RLS
alter table public.user_profiles enable row level security;

-- 3. Define RLS policies
-- Users can view their own profile
create policy "Allow users to view their own profile" on public.user_profiles
    for select using (auth.uid() = id);
-- Users can update their own profile
create policy "Allow users to update their own profile" on public.user_profiles
    for update using (auth.uid() = id) with check (auth.uid() = id);

-- 4. Create a trigger to automatically create a profile for new users
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.user_profiles (id, full_name)
    values (new.id, new.raw_user_meta_data->>'full_name');
    return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();
