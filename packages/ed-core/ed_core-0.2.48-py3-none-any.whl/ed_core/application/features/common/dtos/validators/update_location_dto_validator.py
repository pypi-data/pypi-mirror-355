from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default import (LatitudeValidator,
                                                  LongitudeValidator)

from ed_core.application.features.common.dtos import UpdateLocationDto


class UpdateLocationDtoValidator(ABCValidator[UpdateLocationDto]):
    def __init__(self) -> None:
        self._latitude_validator = LatitudeValidator()
        self._longitude_validator = LongitudeValidator()

    def validate(
        self,
        value: UpdateLocationDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        errors = []

        errors.extend(
            self._longitude_validator.validate(
                value["longitude"], f"{location}.longitude"
            ).errors
        )
        errors.extend(
            self._latitude_validator.validate(
                value["latitude"], f"{location}.latitude"
            ).errors
        )

        if not value["address"]:
            errors.append("Address is required")

        if not value["postal_code"]:
            errors.append("Postal code is required")

        return ValidationResponse(errors)
