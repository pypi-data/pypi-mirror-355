from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default import (NameValidator,
                                                  PhoneNumberValidator)

from ed_core.application.features.common.dtos.validators import \
    CreateLocationDtoValidator
from ed_core.application.features.driver.dtos import CreateDriverDto
from ed_core.application.features.driver.dtos.validators import \
    CreateCarDtoValidator


class CreateDriverDtoValidator(ABCValidator[CreateDriverDto]):
    def __init__(self) -> None:
        self._car_validator = CreateCarDtoValidator()
        self._location_validator = CreateLocationDtoValidator()
        self._name_validator = NameValidator()
        self._phone_number_validator = PhoneNumberValidator()

    def validate(
        self,
        value: CreateDriverDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        errors = []

        errors.extend(
            self._location_validator.validate(
                value["location"], f"{location}.location"
            ).errors
        )
        errors.extend(
            self._phone_number_validator.validate(
                value["phone_number"], f"{location}.phone_number"
            ).errors
        )
        errors.extend(
            self._name_validator.validate(
                value["first_name"], f"{location}.first_name"
            ).errors
        )
        errors.extend(
            self._name_validator.validate(
                value["last_name"], f"{location}.last_name"
            ).errors
        )

        errors.extend(
            self._car_validator.validate(
                value["car"], f"{location}.car").errors
        )

        return ValidationResponse(errors)
