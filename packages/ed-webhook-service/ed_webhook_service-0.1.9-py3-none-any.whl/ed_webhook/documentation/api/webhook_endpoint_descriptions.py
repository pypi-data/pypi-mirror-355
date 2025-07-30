from ed_domain.documentation.api.abc_endpoint_descriptions import \
    ABCEndpointDescriptions
from ed_domain.documentation.api.definitions import (EndpointDescription,
                                                     HttpMethod)


class WebhookEndpointDescriptions(ABCEndpointDescriptions):
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._descriptions: list[EndpointDescription] = [
            {
                "name": "send_webhook",
                "method": HttpMethod.POST,
                "path": f"{self._base_url}/webhooks/{{business_id}}/orders/{{order_id}}",
                "path_params": {"business_id": str, "order_id": str},
            },
        ]

    @property
    def descriptions(self) -> list[EndpointDescription]:
        return self._descriptions
