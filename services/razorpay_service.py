import razorpay
import os
from dotenv import load_dotenv
from core.subscription_config import PLAN_DETAILS

load_dotenv()

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

def create_order(plan: str):
    amount = PLAN_DETAILS[plan]["price"]

    return client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })


def verify_signature(data: dict):
    client.utility.verify_payment_signature(data)
    return True
