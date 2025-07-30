from typing import NotRequired, TypedDict

from ed_core.application.features.common.dtos.update_location_dto import \
    UpdateLocationDto


class UpdateConsumerDto(TypedDict):
    profile_image_url: NotRequired[str]
    location: NotRequired[UpdateLocationDto]
