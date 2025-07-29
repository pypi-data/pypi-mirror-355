from pydantic import BaseModel


class FinishOrderPickUpRequestDto(BaseModel):
    otp: str
