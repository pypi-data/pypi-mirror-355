from abc import ABCMeta, abstractmethod

from ed_domain.documentation.api.definitions import ApiResponse

from ed_core.application.features.business.dtos import (BusinessReportDto,
                                                        CreateApiKeyDto,
                                                        CreateBusinessDto,
                                                        CreateOrderDto,
                                                        UpdateBusinessDto)
from ed_core.application.features.common.dtos import (ApiKeyDto, BusinessDto,
                                                      ConsumerDto,
                                                      CreateConsumerDto,
                                                      DeliveryJobDto,
                                                      DriverDto,
                                                      NotificationDto,
                                                      OrderDto, TrackOrderDto,
                                                      UpdateLocationDto)
from ed_core.application.features.consumer.dtos import UpdateConsumerDto
from ed_core.application.features.delivery_job.dtos import CreateDeliveryJobDto
from ed_core.application.features.driver.dtos import (
    CreateDriverDto, DriverPaymentSummaryDto, FinishOrderDeliveryRequestDto,
    FinishOrderPickUpRequestDto, UpdateDriverDto)


class ABCCoreApiClient(metaclass=ABCMeta):
    # Driver features
    @abstractmethod
    async def get_drivers(self) -> ApiResponse[list[DriverDto]]: ...

    @abstractmethod
    async def create_driver(
        self, create_driver_dto: CreateDriverDto
    ) -> ApiResponse[DriverDto]: ...

    @abstractmethod
    async def get_driver_orders(
        self, driver_id: str
    ) -> ApiResponse[list[OrderDto]]: ...

    @abstractmethod
    async def get_driver_delivery_jobs(
        self, driver_id: str
    ) -> ApiResponse[list[DeliveryJobDto]]: ...

    @abstractmethod
    async def get_driver(self, driver_id: str) -> ApiResponse[DriverDto]: ...

    @abstractmethod
    async def get_driver_payment_summary(
        self, driver_id: str
    ) -> ApiResponse[DriverPaymentSummaryDto]: ...

    @abstractmethod
    async def update_driver(
        self, driver_id: str, update_driver_dto: UpdateDriverDto
    ) -> ApiResponse[DriverDto]: ...

    @abstractmethod
    async def update_driver_current_location(
        self, driver_id: str, update_location_dto: UpdateLocationDto
    ) -> ApiResponse[DriverDto]: ...

    @abstractmethod
    async def get_driver_by_user_id(
        self, user_id: str) -> ApiResponse[DriverDto]: ...

    @abstractmethod
    async def claim_delivery_job(
        self, driver_id: str, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]: ...

    @abstractmethod
    async def cancel_delivery_job(
        self, driver_id: str, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]: ...

    @abstractmethod
    async def start_order_pick_up(
        self, driver_id: str, delivery_job_id: str, order_id: str
    ) -> ApiResponse[None]: ...

    @abstractmethod
    async def finish_order_pick_up(
        self,
        driver_id: str,
        delivery_job_id: str,
        order_id: str,
        finish_order_pick_up_request_dto: FinishOrderPickUpRequestDto,
    ) -> ApiResponse[None]: ...

    @abstractmethod
    async def start_order_delivery(
        self, driver_id: str, delivery_job_id: str, order_id: str
    ) -> ApiResponse[None]: ...

    @abstractmethod
    async def finish_order_delivery(
        self,
        driver_id: str,
        delivery_job_id: str,
        order_id: str,
        finish_order_delivery_request_dto: FinishOrderDeliveryRequestDto,
    ) -> ApiResponse[None]: ...

    # Business features
    @abstractmethod
    async def get_all_businesses(self) -> ApiResponse[list[BusinessDto]]: ...

    @abstractmethod
    async def create_business(
        self, create_business_dto: CreateBusinessDto
    ) -> ApiResponse[BusinessDto]: ...

    @abstractmethod
    async def get_business(
        self, business_id: str) -> ApiResponse[BusinessDto]: ...

    @abstractmethod
    async def update_business(
        self, business_id: str, update_business_dto: UpdateBusinessDto
    ) -> ApiResponse[BusinessDto]: ...

    @abstractmethod
    async def get_business_by_user_id(
        self, user_id: str
    ) -> ApiResponse[BusinessDto]: ...

    @abstractmethod
    async def get_business_orders(
        self, business_id: str
    ) -> ApiResponse[list[OrderDto]]: ...

    @abstractmethod
    async def create_business_order(
        self, business_id: str, create_order_dto: CreateOrderDto
    ) -> ApiResponse[OrderDto]: ...

    @abstractmethod
    async def get_business_api_keys(
        self, business_id: str
    ) -> ApiResponse[list[ApiKeyDto]]: ...

    @abstractmethod
    async def create_business_api_key(
        self, business_id: str, create_api_key_dto: CreateApiKeyDto
    ) -> ApiResponse[ApiKeyDto]: ...

    @abstractmethod
    async def get_business_report(
        self, business_id: str
    ) -> ApiResponse[BusinessReportDto]: ...

    # Delivery job features
    @abstractmethod
    async def get_delivery_jobs(self) -> ApiResponse[list[DeliveryJobDto]]: ...

    @abstractmethod
    async def get_delivery_job(
        self, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]: ...

    @abstractmethod
    async def create_delivery_job(
        self, create_delivery_job_dto: CreateDeliveryJobDto
    ) -> ApiResponse[DeliveryJobDto]: ...

    # Order features
    @abstractmethod
    async def get_orders(self) -> ApiResponse[list[OrderDto]]: ...

    @abstractmethod
    async def track_order(
        self, order_id: str) -> ApiResponse[TrackOrderDto]: ...

    @abstractmethod
    async def get_order(self, order_id: str) -> ApiResponse[OrderDto]: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> ApiResponse[OrderDto]: ...

    # Consumer features
    @abstractmethod
    async def get_consumers(self) -> ApiResponse[list[ConsumerDto]]: ...

    @abstractmethod
    async def create_consumer(
        self, create_consumer_dto: CreateConsumerDto
    ) -> ApiResponse[ConsumerDto]: ...

    @abstractmethod
    async def get_consumer_orders(
        self, consumer_id: str
    ) -> ApiResponse[list[OrderDto]]: ...

    @abstractmethod
    async def get_consumer(
        self, consumer_id: str) -> ApiResponse[ConsumerDto]: ...

    @abstractmethod
    async def update_consumer(
        self, consumer_id: str, update_consumer_dto: UpdateConsumerDto
    ) -> ApiResponse[ConsumerDto]: ...

    @abstractmethod
    async def get_consumer_by_user_id(
        self, user_id: str
    ) -> ApiResponse[ConsumerDto]: ...

    # Notification featuers
    @abstractmethod
    async def get_user_notifications(
        self, user_id: str
    ) -> ApiResponse[list[NotificationDto]]: ...
