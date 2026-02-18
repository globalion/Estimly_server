from fastapi import APIRouter, HTTPException
from datetime import datetime
from database.mongo import db
from schemas.subscription import CreateOrderRequest, VerifyPaymentRequest
from services.razorpay_service import create_order, verify_signature
from services.subscription_service import calculate_dates
from core.subscription_config import PLAN_DETAILS

router = APIRouter(prefix="/subscription", tags=["Subscription"])

subscriptions_collection = db["subscriptions"]
payments_collection = db["payments"]


@router.post("/create-order")
async def create_payment(request: CreateOrderRequest):

    if request.plan not in PLAN_DETAILS:
        raise HTTPException(400, "Invalid plan")

    if request.plan == "free":
        return {"message": "Free plan activated without payment"}

    order = create_order(request.plan)

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": "INR"
    }


@router.post("/verify")
async def verify_payment_route(request: VerifyPaymentRequest):

    try:
        verify_signature({
            "razorpay_order_id": request.razorpay_order_id,
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature
        })
    except:
        raise HTTPException(400, "Invalid signature")

    existing = await subscriptions_collection.find_one(
        {"user_id": request.user_id}
    )

    start_date, end_date = calculate_dates(request.plan, existing)

    await subscriptions_collection.update_one(
        {"user_id": request.user_id},
        {"$set": {
            "plan": request.plan,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active",
            "updated_at": datetime.utcnow()
        }},
        upsert=True
    )

    await payments_collection.insert_one({
        "user_id": request.user_id,
        "plan": request.plan,
        "order_id": request.razorpay_order_id,
        "payment_id": request.razorpay_payment_id,
        "created_at": datetime.utcnow()
    })

    return {
        "message": "Subscription activated",
        "start_date": start_date,
        "end_date": end_date
    }


@router.get("/{user_id}")
async def get_subscription(user_id: str):

    sub = await subscriptions_collection.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )

    if not sub:
        return {"plan": "free"}

    if sub["end_date"] < datetime.utcnow():
        sub["status"] = "expired"

    return sub

