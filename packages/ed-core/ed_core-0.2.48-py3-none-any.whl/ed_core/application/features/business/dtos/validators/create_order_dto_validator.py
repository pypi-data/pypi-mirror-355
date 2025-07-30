from datetime import UTC, datetime

from ed_domain.core.entities.parcel import ParcelSize
from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default import AmountValidator, NameValidator

from ed_core.application.features.business.dtos.create_order_dto import \
    CreateOrderDto


class CreateOrderDtoValidator(ABCValidator[CreateOrderDto]):
    def __init__(self) -> None:
        self._name_validator = NameValidator()
        self._amount_validator = AmountValidator()

    def validate(
        self, value: CreateOrderDto, location: str = ABCValidator.DEFAULT_ERROR_LOCATION
    ) -> ValidationResponse:
        errors = []

        print("DTO", value)
        if value["latest_time_of_delivery"] <= datetime.now(UTC):
            errors.append("Latest time of delivery must be in the future.")

        errors.extend(
            self._amount_validator.validate(
                value["parcel"]["weight"], f"{location}.parcel.weight"
            ).errors
        )
        errors.extend(
            self._amount_validator.validate(
                value["parcel"]["height"], f"{location}.parcel.height"
            ).errors
        )
        errors.extend(
            self._amount_validator.validate(
                value["parcel"]["width"], f"{location}.parcel.width"
            ).errors
        )
        errors.extend(
            self._amount_validator.validate(
                value["parcel"]["length"], f"{location}.parcel.length"
            ).errors
        )

        return ValidationResponse(errors)
