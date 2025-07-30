from ed_domain.common.logging import get_logger
from ed_domain.core.aggregate_roots import Order
from ed_domain.documentation.api.definitions import (EndpointDescription,
                                                     HttpMethod)
from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from ed_infrastructure.documentation.api.endpoint_client import EndpointClient
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_webhook.application.common.responses.base_response import BaseResponse
from ed_webhook.application.features.webhook.requests.commands import \
    SendWebhookCommand

LOG = get_logger()


@request_handler(SendWebhookCommand, BaseResponse[None])
class SendWebhookCommandHandler(RequestHandler):
    def __init__(
        self,
        uow: ABCAsyncUnitOfWork,
    ):
        self._uow = uow

        self._error_message = "Webhook was not sent succesfully."
        self._success_message = "Webhook sent succesfully."

    async def handle(self, request: SendWebhookCommand) -> BaseResponse[None]:
        async with self._uow.transaction():
            business = await self._uow.business_repository.get(id=request.business_id)
            assert business is not None

            if business.webhook is None:
                return BaseResponse[None].success(self._success_message, None)

            order = await self._uow.order_repository.get(id=request.order_id)
            assert order is not None

            endpoint_description: EndpointDescription = {
                "name": "get_all_businesses",
                "method": HttpMethod.POST,
                "path": business.webhook.url,
                "request_model": Order,
            }
            endpoint_client = EndpointClient(endpoint_description)

            await endpoint_client({"request": order})

            return BaseResponse[None].success(self._success_message, None)
