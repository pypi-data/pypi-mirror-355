from ed_domain.validation import ABCValidator, ValidationResponse

from ed_core.application.features.business.dtos.update_business_dto import \
    UpdateBusinessDto
from ed_core.application.features.common.dtos.validators.update_location_dto_validator import \
    UpdateLocationDtoValidator


class UpdateBusinessDtoValidator(ABCValidator[UpdateBusinessDto]):

    def __init__(self) -> None:
        self._update_location_dto_validator = UpdateLocationDtoValidator()

    def validate(
        self,
        value: UpdateBusinessDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        if "location" in value:
            return self._update_location_dto_validator.validate(
                value["location"], f"{location}.location"
            )

        return ValidationResponse([])
