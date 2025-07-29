from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default import (EmailValidator,
                                                  PhoneNumberValidator)

from ed_core.application.features.common.dtos.validators.update_location_dto_validator import \
    UpdateLocationDtoValidator
from ed_core.application.features.driver.dtos.update_driver_dto import \
    UpdateDriverDto


class UpdateDriverDtoValidator(ABCValidator[UpdateDriverDto]):
    def __init__(self) -> None:
        self._location_validator = UpdateLocationDtoValidator()
        self._phone_number_validator = PhoneNumberValidator()
        self._email_validator = EmailValidator()

    def validate(
        self,
        value: UpdateDriverDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        errors = []
        if "location" in value:
            errors.extend(
                self._location_validator.validate(
                    value["location"], f"{location}.location"
                ).errors
            )

        if "email" in value:
            errors.extend(
                self._email_validator.validate(
                    value["email"], f"{location}.email"
                ).errors
            )

        if "phone_number" in value:
            errors.extend(
                self._phone_number_validator.validate(
                    value["phone_number"], f"{location}.phone_number"
                ).errors
            )

        return ValidationResponse(errors)
