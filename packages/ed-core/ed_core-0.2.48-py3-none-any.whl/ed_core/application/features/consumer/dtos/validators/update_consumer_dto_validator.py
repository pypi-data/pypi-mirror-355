from ed_domain.validation import ABCValidator, ValidationResponse

from ed_core.application.features.common.dtos.validators.update_location_dto_validator import \
    UpdateLocationDtoValidator
from ed_core.application.features.consumer.dtos.update_consumer_dto import \
    UpdateConsumerDto


class UpdateConsumerDtoValidator(ABCValidator[UpdateConsumerDto]):
    def __init__(self) -> None:
        self._update_location_dto_validator = UpdateLocationDtoValidator()

    def validate(
        self,
        value: UpdateConsumerDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        if "location" in value:
            return self._update_location_dto_validator.validate(
                value["location"], f"{location}.location"
            )

        return ValidationResponse([])
