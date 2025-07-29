from typing import NotRequired, TypedDict

from ed_core.application.features.common.dtos.update_location_dto import \
    UpdateLocationDto


class UpdateDriverDto(TypedDict):
    profile_image: NotRequired[str]
    phone_number: NotRequired[str]
    email: NotRequired[str]
    location: NotRequired[UpdateLocationDto]
