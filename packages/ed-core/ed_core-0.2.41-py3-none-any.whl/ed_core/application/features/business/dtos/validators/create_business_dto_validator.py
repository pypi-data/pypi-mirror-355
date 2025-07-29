from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default import (EmailValidator,
                                                  NameValidator,
                                                  PhoneNumberValidator)

from ed_core.application.features.business.dtos.create_business_dto import \
    CreateBusinessDto
from ed_core.application.features.driver.dtos.validators.create_driver_dto_validator import \
    CreateLocationDtoValidator


class CreateBusinessDtoValidator(ABCValidator[CreateBusinessDto]):
    def __init__(self) -> None:
        self._location_validator = CreateLocationDtoValidator()
        self._name_validator = NameValidator()
        self._phone_number_validator = PhoneNumberValidator()
        self._email_validator = EmailValidator()

    def validate(
        self,
        value: CreateBusinessDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        errors = []

        errors.extend(
            self._location_validator.validate(
                value["location"], f"{location}.location"
            ).errors
        )

        errors.extend(
            self._name_validator.validate(
                value["business_name"], f"{location}.business_name"
            ).errors
        )
        errors.extend(
            self._name_validator.validate(
                value["owner_first_name"], f"{location}.owner_first_name"
            ).errors
        )
        errors.extend(
            self._name_validator.validate(
                value["owner_last_name"], f"{location}.owner_last_name"
            ).errors
        )
        errors.extend(
            self._phone_number_validator.validate(
                value["phone_number"], f"{location}.phone_number"
            ).errors
        )
        errors.extend(
            self._email_validator.validate(
                value["email"], f"{location}.email").errors
        )

        return ValidationResponse(errors)
