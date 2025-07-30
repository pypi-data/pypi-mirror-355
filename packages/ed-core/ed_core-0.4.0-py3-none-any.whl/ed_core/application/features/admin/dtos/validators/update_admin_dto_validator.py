from ed_domain.validation import ABCValidator, ValidationResponse

from ed_core.application.features.admin.dtos.update_admin_dto import \
    UpdateAdminDto
from ed_core.application.features.common.dtos.validators.update_location_dto_validator import \
    UpdateLocationDtoValidator


class UpdateAdminDtoValidator(ABCValidator[UpdateAdminDto]):
    def __init__(self) -> None:
        self._update_location_dto_validator = UpdateLocationDtoValidator()

    def validate(
        self,
        value: UpdateAdminDto,
        location: str = ABCValidator.DEFAULT_ERROR_LOCATION,
    ) -> ValidationResponse:

        return ValidationResponse([])
