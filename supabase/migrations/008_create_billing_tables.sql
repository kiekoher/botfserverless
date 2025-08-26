-- 008_create_billing_tables.sql

-- 1. Create an ENUM type for subscription status
create type public.subscription_status as enum ('active', 'trialing', 'past_due', 'canceled', 'unpaid');

-- 2. Create the plans table
create table public.plans (
    id text primary key, -- e.g., 'pro_plan'
    name text not null,
    price numeric(10, 2) not null,
    -- The ID of the price object in Stripe (e.g., price_12345)
    stripe_price_id text not null,
    description text
);
comment on table public.plans is 'Defines the available subscription plans.';

-- 3. Create the subscriptions table
create table public.subscriptions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    plan_id text not null references public.plans(id),
    status public.subscription_status not null,

    -- Stripe specific fields
    stripe_customer_id text,
    stripe_subscription_id text unique,

    -- Timestamps
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    current_period_start timestamp with time zone,
    current_period_end timestamp with time zone,
    cancel_at_period_end boolean default false
);
comment on table public.subscriptions is 'Tracks user subscriptions and their status.';

-- 4. Set up indexes
create index on public.subscriptions (user_id);
create index on public.subscriptions (stripe_subscription_id);

-- 5. Enable Row Level Security
alter table public.plans enable row level security;
alter table public.subscriptions enable row level security;

-- 6. Define RLS policies
-- Users can see all plans
create policy "Allow all users to read plans" on public.plans for select using (true);
-- Users can only see and manage their own subscription
create policy "Allow users to manage their own subscription" on public.subscriptions for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- 7. (Optional) Insert some default plans
-- You can pre-populate the plans table if you have fixed plans.
-- Make sure the `stripe_price_id` matches a price object in your Stripe account.
-- Example:
-- insert into public.plans (id, name, price, stripe_price_id, description)
-- values
-- ('free', 'Free Tier', 0.00, 'price_free_tier_id', 'Basic access for free.'),
-- ('pro', 'Pro Tier', 29.00, 'price_pro_tier_id', 'Full access for professionals.');
