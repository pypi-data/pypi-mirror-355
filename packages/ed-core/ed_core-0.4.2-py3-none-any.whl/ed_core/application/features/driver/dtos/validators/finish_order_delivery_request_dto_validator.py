from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default.otp_validator import OtpValidator

from ed_core.application.features.driver.dtos.finish_order_delivery_request_dto import \
    FinishOrderDeliveryRequestDto


class FinishOrderDeliveryRequestDtoValidator(
    ABCValidator[FinishOrderDeliveryRequestDto]
):
    def __init__(self) -> None:
        self._otp_validator = OtpValidator()

    def validate(
        self,
        value: FinishOrderDeliveryRequestDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        return self._otp_validator.validate(value.otp, f"{location}.otp")
