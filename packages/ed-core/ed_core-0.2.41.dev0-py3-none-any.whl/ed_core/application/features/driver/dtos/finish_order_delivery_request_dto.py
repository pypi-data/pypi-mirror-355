from pydantic import BaseModel


class FinishOrderDeliveryRequestDto(BaseModel):
    otp: str
