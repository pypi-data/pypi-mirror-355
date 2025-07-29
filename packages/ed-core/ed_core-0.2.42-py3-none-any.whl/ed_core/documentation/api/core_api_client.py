from ed_domain.documentation.api.definitions import ApiResponse
from ed_infrastructure.documentation.api.endpoint_client import EndpointClient

from ed_core.application.features.business.dtos import (BusinessReportDto,
                                                        CreateApiKeyDto,
                                                        CreateBusinessDto,
                                                        CreateOrderDto,
                                                        UpdateBusinessDto)
from ed_core.application.features.common.dtos import (BusinessDto, ConsumerDto,
                                                      CreateConsumerDto,
                                                      DeliveryJobDto,
                                                      DriverDto,
                                                      NotificationDto,
                                                      OrderDto, TrackOrderDto,
                                                      UpdateLocationDto)
from ed_core.application.features.common.dtos.api_key_dto import ApiKeyDto
from ed_core.application.features.consumer.dtos import UpdateConsumerDto
from ed_core.application.features.delivery_job.dtos import CreateDeliveryJobDto
from ed_core.application.features.driver.dtos import (
    CreateDriverDto, DriverPaymentSummaryDto, FinishOrderDeliveryRequestDto,
    FinishOrderPickUpRequestDto, UpdateDriverDto)
from ed_core.documentation.api.abc_core_api_client import ABCCoreApiClient
from ed_core.documentation.api.core_endpoint_descriptions import \
    CoreEndpointDescriptions


class CoreApiClient(ABCCoreApiClient):
    def __init__(self, core_api: str) -> None:
        self._endpoints = CoreEndpointDescriptions(core_api)

    async def get_drivers(self) -> ApiResponse[list[DriverDto]]:
        endpoint = self._endpoints.get_description("get_drivers")
        api_client = EndpointClient[list[DriverDto]](endpoint)

        return await api_client({})

    async def create_driver(
        self, create_driver_dto: CreateDriverDto
    ) -> ApiResponse[DriverDto]:
        endpoint = self._endpoints.get_description("create_driver")
        api_client = EndpointClient[DriverDto](endpoint)

        return await api_client({"request": create_driver_dto})

    async def get_driver_orders(self, driver_id: str) -> ApiResponse[list[OrderDto]]:
        endpoint = self._endpoints.get_description("get_driver_orders")
        api_client = EndpointClient[list[OrderDto]](endpoint)
        return await api_client({"path_params": {"driver_id": driver_id}})

    async def get_driver_delivery_jobs(
        self, driver_id: str
    ) -> ApiResponse[list[DeliveryJobDto]]:
        endpoint = self._endpoints.get_description("get_driver_delivery_jobs")
        api_client = EndpointClient[list[DeliveryJobDto]](endpoint)
        return await api_client({"path_params": {"driver_id": driver_id}})

    async def get_driver_by_user_id(self, user_id: str) -> ApiResponse[DriverDto]:
        endpoint = self._endpoints.get_description("get_driver_by_user_id")
        api_client = EndpointClient[DriverDto](endpoint)
        return await api_client({"path_params": {"user_id": user_id}})

    async def get_driver_payment_summary(
        self, driver_id: str
    ) -> ApiResponse[DriverPaymentSummaryDto]:
        endpoint = self._endpoints.get_description(
            "get_driver_payment_summary")
        api_client = EndpointClient[DriverPaymentSummaryDto](endpoint)
        return await api_client({"path_params": {"driver_id": driver_id}})

    async def get_driver(self, driver_id: str) -> ApiResponse[DriverDto]:
        endpoint = self._endpoints.get_description("get_driver")
        api_client = EndpointClient[DriverDto](endpoint)
        return await api_client({"path_params": {"driver_id": driver_id}})

    async def update_driver(
        self, driver_id: str, update_driver_dto: UpdateDriverDto
    ) -> ApiResponse[DriverDto]:
        endpoint = self._endpoints.get_description("update_driver")
        api_client = EndpointClient[DriverDto](endpoint)
        return await api_client(
            {"path_params": {"driver_id": driver_id}, "request": update_driver_dto}
        )

    async def update_driver_current_location(
        self, driver_id: str, update_location_dto: UpdateLocationDto
    ) -> ApiResponse[DriverDto]:
        endpoint = self._endpoints.get_description(
            "update_driver_current_location")
        api_client = EndpointClient[DriverDto](endpoint)
        return await api_client(
            {"path_params": {"driver_id": driver_id},
                "request": update_location_dto}
        )

    async def claim_delivery_job(
        self, driver_id: str, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]:
        endpoint = self._endpoints.get_description("claim_delivery_job")
        api_client = EndpointClient[DeliveryJobDto](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                }
            }
        )

    async def cancel_delivery_job(
        self, driver_id: str, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]:
        endpoint = self._endpoints.get_description("cancel_delivery_job")
        api_client = EndpointClient[DeliveryJobDto](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                }
            }
        )

    async def start_order_pick_up(
        self, driver_id: str, delivery_job_id: str, order_id: str
    ) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("start_order_pick_up")
        api_client = EndpointClient[None](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                    "order_id": order_id,
                }
            }
        )

    async def finish_order_pick_up(
        self,
        driver_id: str,
        delivery_job_id: str,
        order_id: str,
        finish_order_pick_up_request_dto: FinishOrderPickUpRequestDto,
    ) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("finish_order_pick_up")
        api_client = EndpointClient[None](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                    "order_id": order_id,
                },
                "request": finish_order_pick_up_request_dto,
            }
        )

    async def start_order_delivery(
        self, driver_id: str, delivery_job_id: str, order_id: str
    ) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("start_order_delivery")
        api_client = EndpointClient[None](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                    "order_id": order_id,
                }
            }
        )

    async def finish_order_delivery(
        self,
        driver_id: str,
        delivery_job_id: str,
        order_id: str,
        finish_order_delivery_request_dto: FinishOrderDeliveryRequestDto,
    ) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("finish_order_delivery")
        api_client = EndpointClient[None](endpoint)
        return await api_client(
            {
                "path_params": {
                    "driver_id": driver_id,
                    "delivery_job_id": delivery_job_id,
                    "order_id": order_id,
                },
                "request": finish_order_delivery_request_dto,
            }
        )

    async def get_all_businesses(self) -> ApiResponse[list[BusinessDto]]:
        endpoint = self._endpoints.get_description("get_all_businesses")
        api_client = EndpointClient[list[BusinessDto]](endpoint)
        return await api_client({})

    async def create_business(
        self, create_business_dto: CreateBusinessDto
    ) -> ApiResponse[BusinessDto]:
        endpoint = self._endpoints.get_description("create_a_business")
        print("CREATE BUSINESS ENDPOINT:", endpoint)
        api_client = EndpointClient[BusinessDto](endpoint)
        return await api_client({"request": create_business_dto})

    async def get_business_by_user_id(self, user_id: str) -> ApiResponse[BusinessDto]:
        endpoint = self._endpoints.get_description("get_business_by_user_id")
        api_client = EndpointClient[BusinessDto](endpoint)
        return await api_client({"path_params": {"user_id": user_id}})

    async def get_business(self, business_id: str) -> ApiResponse[BusinessDto]:
        endpoint = self._endpoints.get_description("get_business")
        api_client = EndpointClient[BusinessDto](endpoint)
        return await api_client({"path_params": {"business_id": business_id}})

    async def update_business(
        self, business_id: str, update_business_dto: UpdateBusinessDto
    ) -> ApiResponse[BusinessDto]:
        endpoint = self._endpoints.get_description("updaate_business")
        api_client = EndpointClient[BusinessDto](endpoint)
        return await api_client(
            {
                "path_params": {"business_id": business_id},
                "request": update_business_dto,
            }
        )

    async def get_business_orders(
        self, business_id: str
    ) -> ApiResponse[list[OrderDto]]:
        endpoint = self._endpoints.get_description("get_business_orders")
        api_client = EndpointClient[list[OrderDto]](endpoint)
        return await api_client({"path_params": {"business_id": business_id}})

    async def create_business_order(
        self, business_id: str, create_order_dto: CreateOrderDto
    ) -> ApiResponse[OrderDto]:
        endpoint = self._endpoints.get_description("create_business_orders")
        api_client = EndpointClient[OrderDto](endpoint)
        return await api_client(
            {"path_params": {"business_id": business_id}, "request": create_order_dto}
        )

    async def get_business_api_keys(
        self, business_id: str
    ) -> ApiResponse[list[ApiKeyDto]]:
        endpoint = self._endpoints.get_description("get_business_api_keys")
        api_client = EndpointClient[list[ApiKeyDto]](endpoint)
        return await api_client({"path_params": {"business_id": business_id}})

    async def get_business_report(
        self, business_id: str
    ) -> ApiResponse[BusinessReportDto]:
        endpoint = self._endpoints.get_description("get_business_api_keys")
        api_client = EndpointClient[BusinessReportDto](endpoint)
        return await api_client({"path_params": {"business_id": business_id}})

    async def create_business_api_key(
        self, business_id: str, create_api_key_dto: CreateApiKeyDto
    ) -> ApiResponse[ApiKeyDto]:
        endpoint = self._endpoints.get_description("create_business_api_key")
        api_client = EndpointClient[ApiKeyDto](endpoint)
        return await api_client(
            {"path_params": {"business_id": business_id},
                "request": create_api_key_dto}
        )

    async def get_delivery_jobs(self) -> ApiResponse[list[DeliveryJobDto]]:
        endpoint = self._endpoints.get_description("get_delivery_jobs")
        api_client = EndpointClient[list[DeliveryJobDto]](endpoint)
        return await api_client({})

    async def get_delivery_job(
        self, delivery_job_id: str
    ) -> ApiResponse[DeliveryJobDto]:
        endpoint = self._endpoints.get_description("get_delivery_job")
        api_client = EndpointClient[DeliveryJobDto](endpoint)
        return await api_client({"path_params": {"delivery_job_id": delivery_job_id}})

    async def create_delivery_job(
        self, create_delivery_job_dto: CreateDeliveryJobDto
    ) -> ApiResponse[DeliveryJobDto]:
        endpoint = self._endpoints.get_description("create_delivery_job")
        api_client = EndpointClient[DeliveryJobDto](endpoint)
        return await api_client({"request": create_delivery_job_dto})

    async def get_orders(self) -> ApiResponse[list[OrderDto]]:
        endpoint = self._endpoints.get_description("get_orders")
        api_client = EndpointClient[list[OrderDto]](endpoint)
        return await api_client({})

    async def get_order(self, order_id: str) -> ApiResponse[OrderDto]:
        endpoint = self._endpoints.get_description("get_order")
        api_client = EndpointClient[OrderDto](endpoint)
        return await api_client({"path_params": {"order_id": order_id}})

    async def track_order(self, order_id: str) -> ApiResponse[TrackOrderDto]:
        endpoint = self._endpoints.get_description("track_order")
        api_client = EndpointClient[TrackOrderDto](endpoint)
        return await api_client({"path_params": {"order_id": order_id}})

    async def cancel_order(self, order_id: str) -> ApiResponse[OrderDto]:
        endpoint = self._endpoints.get_description("cancel_order")
        api_client = EndpointClient[OrderDto](endpoint)
        return await api_client({"path_params": {"order_id": order_id}})

    async def get_consumers(self) -> ApiResponse[list[ConsumerDto]]:
        endpoint = self._endpoints.get_description("get_consumers")
        api_client = EndpointClient[list[ConsumerDto]](endpoint)

        return await api_client({})

    async def create_consumer(
        self, create_consumer_dto: CreateConsumerDto
    ) -> ApiResponse[ConsumerDto]:
        endpoint = self._endpoints.get_description("create_consumer")
        api_client = EndpointClient[ConsumerDto](endpoint)

        return await api_client({"request": create_consumer_dto})

    async def get_consumer_orders(
        self, consumer_id: str
    ) -> ApiResponse[list[OrderDto]]:
        endpoint = self._endpoints.get_description("get_consumer_orders")
        api_client = EndpointClient[list[OrderDto]](endpoint)
        return await api_client({"path_params": {"consumer_id": consumer_id}})

    async def get_consumer_by_user_id(self, user_id: str) -> ApiResponse[ConsumerDto]:
        endpoint = self._endpoints.get_description("get_consumer_by_user_id")
        api_client = EndpointClient[ConsumerDto](endpoint)
        return await api_client({"path_params": {"user_id": user_id}})

    async def get_consumer(self, consumer_id: str) -> ApiResponse[ConsumerDto]:
        endpoint = self._endpoints.get_description("get_consumer")
        api_client = EndpointClient[ConsumerDto](endpoint)
        return await api_client({"path_params": {"consumer_id": consumer_id}})

    async def update_consumer(
        self, consumer_id: str, update_consumer_dto: UpdateConsumerDto
    ) -> ApiResponse[ConsumerDto]:
        endpoint = self._endpoints.get_description("update_consumer")
        api_client = EndpointClient[ConsumerDto](endpoint)
        return await api_client(
            {
                "path_params": {"consumer_id": consumer_id},
                "request": update_consumer_dto,
            }
        )

    async def get_user_notifications(
        self, user_id: str
    ) -> ApiResponse[list[NotificationDto]]:
        endpoint = self._endpoints.get_description("get_user_notifications")
        api_client = EndpointClient[list[NotificationDto]](endpoint)
        return await api_client({"path_params": {"user_id": user_id}})


if __name__ == "__main__":
    CoreApiClient("")
