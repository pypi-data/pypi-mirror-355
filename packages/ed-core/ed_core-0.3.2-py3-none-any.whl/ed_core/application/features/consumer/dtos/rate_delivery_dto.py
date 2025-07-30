from typing import Literal, TypedDict


class RateDeliveryDto(TypedDict):
    rating: Literal[1, 2, 3, 4, 5]
