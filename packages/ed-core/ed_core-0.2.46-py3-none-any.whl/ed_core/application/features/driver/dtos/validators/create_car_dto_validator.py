from ed_domain.validation import ABCValidator, ValidationResponse

from ed_core.application.features.driver.dtos.create_car_dto import \
    CreateCarDto


class CreateCarDtoValidator(ABCValidator[CreateCarDto]):
    def validate(
        self, value: CreateCarDto, location: str = ABCValidator.DEFAULT_ERROR_LOCATION
    ) -> ValidationResponse:
        errors = []

        return ValidationResponse()
