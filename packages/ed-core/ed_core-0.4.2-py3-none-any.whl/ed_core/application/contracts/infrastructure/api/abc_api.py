from abc import ABCMeta, abstractmethod

from ed_auth.documentation.api.abc_auth_api_client import ABCAuthApiClient
from ed_notification.documentation.api.abc_notification_api_client import \
    ABCNotificationApiClient
from ed_optimization.documentation.api.abc_optimization_api_client import \
    ABCOptimizationApiClient
from ed_webhook.documentation.api.abc_webhook_api_client import \
    ABCWebhookApiClient


class ABCApi(metaclass=ABCMeta):
    @property
    @abstractmethod
    def auth_api(self) -> ABCAuthApiClient: ...

    @property
    @abstractmethod
    def notification_api(self) -> ABCNotificationApiClient: ...

    @property
    @abstractmethod
    def optimization_api(self) -> ABCOptimizationApiClient: ...

    @property
    @abstractmethod
    def webhook_api(self) -> ABCWebhookApiClient: ...
