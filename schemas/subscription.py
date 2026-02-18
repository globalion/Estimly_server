from pydantic import BaseModel

class CreateOrderRequest(BaseModel):
    user_id: str
    plan: str


class VerifyPaymentRequest(BaseModel):
    user_id: str
    plan: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
