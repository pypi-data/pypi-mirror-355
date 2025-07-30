from abc import ABCMeta, abstractmethod
from uuid import UUID

from ed_domain.documentation.api.definitions import ApiResponse


class ABCWebhookApiClient(metaclass=ABCMeta):
    @abstractmethod
    async def send_webhook(
        self, business_id: UUID, order_id: UUID
    ) -> ApiResponse[None]: ...
