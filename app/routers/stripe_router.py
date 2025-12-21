from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import stripe
import os
from datetime import datetime, timedelta
from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..plan_config import PLAN_LIMITS

router = APIRouter(prefix="/stripe", tags=["stripe"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Plan to Stripe Price ID mapping (you'll need to create these in Stripe Dashboard)
STRIPE_PRICE_IDS = {
    "starter": os.getenv("STRIPE_PRICE_STARTER", "price_starter"),    # 7.99€/mois
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_pro"),                # 17.99€/mois
    "business": os.getenv("STRIPE_PRICE_BUSINESS", "price_business"), # 44.99€/mois
    # Anciens noms pour compatibilité
    "standard": os.getenv("STRIPE_PRICE_STARTER", "price_starter"),
    "premium": os.getenv("STRIPE_PRICE_PRO", "price_pro"),
    "agency": os.getenv("STRIPE_PRICE_BUSINESS", "price_business")
}

# Pydantic models
class CheckoutSessionRequest(BaseModel):
    plan: str  # standard, premium, agency
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    session_id: str
    url: str

class PortalSessionRequest(BaseModel):
    return_url: str

class PortalSessionResponse(BaseModel):
    url: str

class SubscriptionInfo(BaseModel):
    plan: str
    status: str
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    stripe_customer_id: Optional[str]

class PaymentIntentRequest(BaseModel):
    plan: str  # starter, pro, business

class PaymentIntentResponse(BaseModel):
    client_secret: str
    publishable_key: str


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Checkout session for subscription"""
    try:
        print(f"🔍 Creating checkout session for plan: {request.plan}")
        print(f"🔍 Available plans: {list(STRIPE_PRICE_IDS.keys())}")
        print(f"🔍 Price ID for {request.plan}: {STRIPE_PRICE_IDS.get(request.plan)}")

        # Validate plan
        if request.plan not in STRIPE_PRICE_IDS:
            print(f"❌ Invalid plan: {request.plan}")
            raise HTTPException(status_code=400, detail=f"Plan invalide: {request.plan}. Plans disponibles: {list(STRIPE_PRICE_IDS.keys())}")

        # Check if user already has a Stripe customer ID
        customer_id = current_user.stripe_customer_id

        # If no customer exists, create one
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={
                    "user_id": current_user.id
                }
            )
            customer_id = customer.id

            # Save customer ID to database
            current_user.stripe_customer_id = customer_id
            db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": STRIPE_PRICE_IDS[request.plan],
                "quantity": 1,
            }],
            mode="subscription",
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata={
                "user_id": current_user.id,
                "plan": request.plan
            },
            subscription_data={
                "metadata": {
                    "user_id": current_user.id,
                    "plan": request.plan
                }
            }
        )

        return CheckoutSessionResponse(
            session_id=checkout_session.id,
            url=checkout_session.url
        )

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ General error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la session: {str(e)}")


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Payment Intent for embedded checkout with Payment Element"""
    try:
        print(f"🔍 Creating payment intent for plan: {request.plan}")

        # Validate plan
        if request.plan not in STRIPE_PRICE_IDS:
            raise HTTPException(status_code=400, detail=f"Plan invalide: {request.plan}")

        # Get or create Stripe customer
        customer_id = current_user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": current_user.id}
            )
            customer_id = customer.id
            current_user.stripe_customer_id = customer_id
            db.commit()

        # Get price details to determine amount
        price_id = STRIPE_PRICE_IDS[request.plan]
        price = stripe.Price.retrieve(price_id)

        # Create subscription with payment intent
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
            metadata={
                "user_id": current_user.id,
                "plan": request.plan
            }
        )

        # Get client secret from payment intent
        payment_intent = subscription.latest_invoice.payment_intent
        client_secret = payment_intent.client_secret

        # Store subscription ID temporarily
        current_user.stripe_subscription_id = subscription.id
        db.commit()

        # Get publishable key
        publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        if not publishable_key:
            raise Exception("STRIPE_PUBLISHABLE_KEY not configured in environment variables")

        print(f"✅ Payment intent created successfully")
        print(f"✅ Client secret: {client_secret[:20]}...")
        print(f"✅ Publishable key: {publishable_key[:20]}...")

        return PaymentIntentResponse(
            client_secret=client_secret,
            publishable_key=publishable_key
        )

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ General error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du payment intent: {str(e)}")


@router.post("/create-portal-session", response_model=PortalSessionResponse)
async def create_portal_session(
    request: PortalSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe Customer Portal session for managing subscription"""
    try:
        if not current_user.stripe_customer_id:
            raise HTTPException(status_code=400, detail="Aucun abonnement actif")

        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=request.return_url,
        )

        return PortalSessionResponse(url=portal_session.url)

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de la session portal: {str(e)}")


@router.get("/subscription-info", response_model=SubscriptionInfo)
async def get_subscription_info(
    current_user: User = Depends(get_current_user)
):
    """Get current subscription information"""
    try:
        if not current_user.stripe_subscription_id:
            return SubscriptionInfo(
                plan=current_user.current_plan,
                status="inactive",
                current_period_end=None,
                cancel_at_period_end=False,
                stripe_customer_id=current_user.stripe_customer_id
            )

        # Retrieve subscription from Stripe
        subscription = stripe.Subscription.retrieve(current_user.stripe_subscription_id)

        return SubscriptionInfo(
            plan=current_user.current_plan,
            status=subscription.status,
            current_period_end=datetime.fromtimestamp(subscription.current_period_end),
            cancel_at_period_end=subscription.cancel_at_period_end,
            stripe_customer_id=current_user.stripe_customer_id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération de l'abonnement: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks"""
    print(f"🔔 Webhook received at {datetime.utcnow()}")

    try:
        # Get the raw body
        payload = await request.body()
        print(f"📦 Payload size: {len(payload)} bytes")

        # Check if webhook secret is configured
        if not STRIPE_WEBHOOK_SECRET:
            print("❌ STRIPE_WEBHOOK_SECRET not configured!")
            return {"status": "error", "message": "Webhook secret not configured"}

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
            print(f"✅ Signature verified for event: {event.type}")
        except ValueError as e:
            print(f"❌ Invalid payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            print(f"❌ Invalid signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        print(f"🔄 Processing event type: {event.type}")

        if event.type == "checkout.session.completed":
            session = event.data.object
            await handle_checkout_completed(session, db)

        elif event.type == "customer.subscription.created":
            subscription = event.data.object
            await handle_subscription_created(subscription, db)

        elif event.type == "customer.subscription.updated":
            subscription = event.data.object
            await handle_subscription_updated(subscription, db)

        elif event.type == "customer.subscription.deleted":
            subscription = event.data.object
            await handle_subscription_deleted(subscription, db)

        elif event.type == "invoice.payment_succeeded":
            invoice = event.data.object
            await handle_invoice_paid(invoice, db)

        elif event.type == "invoice.payment_failed":
            invoice = event.data.object
            await handle_invoice_failed(invoice, db)
        else:
            print(f"ℹ️  Unhandled event type: {event.type}")

        print(f"✅ Webhook processed successfully: {event.type}")
        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        # Return 200 to prevent Stripe from retrying on temporary errors
        return {"status": "error", "message": str(e)}


# Helper functions for webhook handlers
async def handle_checkout_completed(session, db: Session):
    """Handle successful checkout"""
    user_id = int(session.metadata.get("user_id"))
    plan = session.metadata.get("plan")

    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.stripe_customer_id = session.customer
        user.current_plan = plan
        user.plan_started_at = datetime.utcnow()
        user.subscription_status = "active"

        # Reset credits based on plan
        user.credits_remaining = PLAN_LIMITS[plan]["credits"]
        user.last_credit_renewal = datetime.utcnow()

        db.commit()
        print(f"Checkout completed for user {user_id}, plan {plan}")


async def handle_subscription_created(subscription, db: Session):
    """Handle new subscription creation"""
    customer_id = subscription.customer

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.stripe_subscription_id = subscription.id
        user.subscription_status = subscription.status
        user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)

        db.commit()
        print(f"Subscription created for user {user.id}")


async def handle_subscription_updated(subscription, db: Session):
    """Handle subscription updates"""
    customer_id = subscription.customer

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.subscription_status = subscription.status
        user.subscription_end_date = datetime.fromtimestamp(subscription.current_period_end)

        # If subscription is canceled, handle it
        if subscription.cancel_at_period_end:
            print(f"Subscription will be canceled at period end for user {user.id}")

        db.commit()
        print(f"Subscription updated for user {user.id}")


async def handle_subscription_deleted(subscription, db: Session):
    """Handle subscription cancellation"""
    customer_id = subscription.customer

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.stripe_subscription_id = None
        user.subscription_status = "canceled"
        user.current_plan = "free"
        user.credits_remaining = PLAN_LIMITS["free"]["max_requests"]

        db.commit()
        print(f"Subscription deleted for user {user.id}")


async def handle_invoice_paid(invoice, db: Session):
    """Handle successful payment (monthly renewal)"""
    customer_id = invoice.customer

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user and user.current_plan != "free":
        # Renew credits
        user.credits_remaining = PLAN_LIMITS[user.current_plan]["max_requests"]
        user.last_credit_renewal = datetime.utcnow()

        db.commit()
        print(f"Invoice paid, credits renewed for user {user.id}")


async def handle_invoice_failed(invoice, db: Session):
    """Handle failed payment"""
    customer_id = invoice.customer

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if user:
        user.subscription_status = "past_due"

        db.commit()
        print(f"Invoice payment failed for user {user.id}")
