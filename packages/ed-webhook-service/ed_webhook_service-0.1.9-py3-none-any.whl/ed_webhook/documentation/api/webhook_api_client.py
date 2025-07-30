from uuid import UUID

from ed_domain.documentation.api.definitions import ApiResponse
from ed_infrastructure.documentation.api.endpoint_client import EndpointClient

from ed_webhook.documentation.api.abc_webhook_api_client import \
    ABCWebhookApiClient
from ed_webhook.documentation.api.webhook_endpoint_descriptions import \
    WebhookEndpointDescriptions


class WebhookApiClient(ABCWebhookApiClient):
    def __init__(self, webhook_api: str) -> None:
        self._endpoints = WebhookEndpointDescriptions(webhook_api)

    async def send_webhook(
        self, business_id: UUID, order_id: UUID
    ) -> ApiResponse[None]:
        endpoint = self._endpoints.get_description("send_webhook")
        api_client = EndpointClient[None](endpoint)

        return await api_client(
            {
                "path_params": {
                    "business_id": business_id,
                    "order_id": order_id,
                }
            }
        )
