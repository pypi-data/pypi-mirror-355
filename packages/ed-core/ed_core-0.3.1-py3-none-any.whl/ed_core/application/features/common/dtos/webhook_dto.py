from pydantic import BaseModel


class WebhookDto(BaseModel):
    url: str
