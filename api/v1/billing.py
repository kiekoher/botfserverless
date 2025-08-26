import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from datetime import datetime

from core.config import get_settings, Settings
from dependencies import get_current_user_id, get_supabase_adapter
from infrastructure.supabase_adapter import SupabaseAdapter

router = APIRouter(tags=["Billing"])

class CheckoutSessionRequest(BaseModel):
    price_id: str # The Stripe price ID, e.g., price_12345
    plan_id: str # The internal plan ID from our DB, e.g., 'pro'

# === Public Endpoint to list plans ===

@router.get("/plans")
async def list_available_plans(adapter: SupabaseAdapter = Depends(get_supabase_adapter)):
    """Lists all available subscription plans from the database."""
    try:
        plans = await adapter.client.from_("plans").select("*").execute()
        return plans.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plans: {e}")

# === Authenticated Endpoints ===

@router.get("/subscription")
async def get_my_subscription(
    user_id: str = Depends(get_current_user_id),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Retrieves the subscription details for the authenticated user."""
    try:
        subscription = await adapter.get_subscription_for_user(user_id=user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found for this user.")
        return subscription
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-checkout-session")
async def create_checkout_session(
    payload: CheckoutSessionRequest,
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Creates a Stripe Checkout session for a user to subscribe to a plan."""
    try:
        customer_id = await adapter.get_stripe_customer_id(user_id)

        session_params = {
            "payment_method_types": ["card"],
            "line_items": [{"price": payload.price_id, "quantity": 1}],
            "mode": "subscription",
            "success_url": f"{settings.frontend_url}/dashboard?payment_success=true",
            "cancel_url": f"{settings.frontend_url}/dashboard?payment_canceled=true",
            "metadata": {
                "user_id": user_id,
                "plan_id": payload.plan_id
            }
        }

        if customer_id:
            session_params["customer"] = customer_id
        else:
            # Pass user_id in customer_creation metadata to link them in the webhook
            session_params["customer_creation"] = "always"
            # You can pre-fill the email if you have it
            # user_email = await adapter.get_user_email(user_id)
            # session_params["customer_email"] = user_email

        checkout_session = stripe.checkout.Session.create(**session_params)
        return {"sessionId": checkout_session.id, "url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")


@router.post("/create-customer-portal-session")
async def create_customer_portal_session(
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
):
    """Creates a Stripe Billing Portal session for a user to manage their subscription."""
    try:
        customer_id = await adapter.get_stripe_customer_id(user_id)
        if not customer_id:
            raise HTTPException(status_code=404, detail="User does not have a Stripe customer ID.")

        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.frontend_url}/dashboard/settings/billing",
        )
        return {"url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e}")


# === Webhook Endpoint ===

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    adapter: SupabaseAdapter = Depends(get_supabase_adapter),
    settings: Settings = Depends(get_settings),
):
    """Handles incoming webhooks from Stripe to update subscription statuses."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")

    # Handle the event
    data = event["data"]["object"]
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        if data["mode"] == "subscription":
            customer_id = data["customer"]
            user_id = data["metadata"]["user_id"]
            plan_id = data["metadata"]["plan_id"]
            stripe_subscription_id = data["subscription"]

            # Retrieve full subscription object to get all details
            sub_data = stripe.Subscription.retrieve(stripe_subscription_id)

            await adapter.create_subscription(
                user_id=user_id,
                plan_id=plan_id,
                status=sub_data["status"],
                stripe_subscription_id=sub_data["id"],
                stripe_customer_id=customer_id,
                current_period_start=datetime.utcfromtimestamp(sub_data["current_period_start"]).isoformat(),
                current_period_end=datetime.utcfromtimestamp(sub_data["current_period_end"]).isoformat(),
                cancel_at_period_end=sub_data["cancel_at_period_end"],
            )

    elif event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        await adapter.update_subscription_status(
            stripe_subscription_id=data["id"],
            new_status=data["status"],
            cancel_at_period_end=data["cancel_at_period_end"],
            current_period_start=datetime.utcfromtimestamp(data["current_period_start"]).isoformat(),
            current_period_end=datetime.utcfromtimestamp(data["current_period_end"]).isoformat(),
        )

    else:
        print(f"Unhandled webhook event type: {event_type}")

    return Response(status_code=200)
