-- 009_add_usage_quotas.sql

-- 1. Add credit limit to plans table
alter table public.plans
add column if not exists monthly_credit_limit integer default 0;

comment on column public.plans.monthly_credit_limit is 'The number of monthly message credits included in this plan.';

-- 2. Add credit balance to subscriptions table
alter table public.subscriptions
add column if not exists message_credits integer default 0;

comment on column public.subscriptions.message_credits is 'The remaining message credits for the current billing period.';

-- 3. Update RLS policies for plans to keep it public
-- No changes needed if the policy is `using (true)`.

-- 4. Insert/Update default plans with limits
-- This is an idempotent way to insert/update plans.
insert into public.plans (id, name, price, stripe_price_id, description, monthly_credit_limit)
values
    ('free', 'Free Tier', 0.00, 'price_free_tier_id', 'Basic access for free.', 50),
    ('pro', 'Pro Tier', 29.00, 'price_pro_tier_id', 'Full access for professionals.', 500)
on conflict (id) do update set
    name = excluded.name,
    price = excluded.price,
    stripe_price_id = excluded.stripe_price_id,
    description = excluded.description,
    monthly_credit_limit = excluded.monthly_credit_limit;

-- Note: We need a mechanism to reset credits monthly.
-- This can be done via a pg_cron job or a webhook handler when a subscription renews.
-- For now, we will handle credit decrement in the application logic.

-- Example of a function to reset credits, which could be called by a cron job.
create or replace function reset_monthly_credits()
returns void as $$
begin
    update subscriptions s
    set message_credits = p.monthly_credit_limit
    from plans p
    where s.plan_id = p.id
    and s.status = 'active'
    -- This condition is tricky. It should only run once per billing cycle.
    -- A more robust solution would track the last reset date.
    and s.current_period_end >= now(); -- Simplified logic
end;
$$ language plpgsql;

-- Function to safely decrement credits and check balance
create or replace function decrement_credits(p_user_id uuid, p_amount int)
returns table (success boolean, new_credits int) as $$
declare
    current_credits int;
    sub_id uuid;
begin
    -- Find the user's active subscription
    select id into sub_id from public.subscriptions
    where user_id = p_user_id and status = 'active'
    limit 1;

    if sub_id is null then
        return query select false, 0;
        return;
    end if;

    -- Lock the row and decrement credits
    update public.subscriptions
    set message_credits = message_credits - p_amount
    where id = sub_id and message_credits >= p_amount
    returning message_credits into current_credits;

    if found then
        return query select true, current_credits;
    else
        select message_credits into current_credits from public.subscriptions where id = sub_id;
        return query select false, current_credits;
    end if;
end;
$$ language plpgsql security definer;
