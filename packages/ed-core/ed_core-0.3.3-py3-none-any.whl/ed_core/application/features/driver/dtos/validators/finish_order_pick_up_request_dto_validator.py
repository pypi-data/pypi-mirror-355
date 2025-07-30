from ed_domain.validation import ABCValidator, ValidationResponse
from ed_infrastructure.validation.default.otp_validator import OtpValidator

from ed_core.application.features.driver.dtos.finish_order_pick_up_request_dto import \
    FinishOrderPickUpRequestDto


class FinishOrderPickUpRequestDtoValidator(ABCValidator[FinishOrderPickUpRequestDto]):
    def __init__(self) -> None:
        self._otp_validator = OtpValidator()

    def validate(
        self,
        value: FinishOrderPickUpRequestDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:
        return self._otp_validator.validate(value.otp, f"{location}.otp")
