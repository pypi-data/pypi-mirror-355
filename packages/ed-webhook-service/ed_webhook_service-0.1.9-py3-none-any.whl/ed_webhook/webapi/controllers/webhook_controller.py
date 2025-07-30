from uuid import UUID

from fastapi import APIRouter, Depends
from rmediator.decorators.request_handler import Annotated
from rmediator.mediator import Mediator

from ed_webhook.application.common.responses.base_response import BaseResponse
from ed_webhook.application.features.webhook.requests.commands import \
    SendWebhookCommand
from ed_webhook.common.logging_helpers import get_logger
from ed_webhook.webapi.common.helpers import GenericResponse, rest_endpoint
from ed_webhook.webapi.dependency_setup import mediator

LOG = get_logger()
router = APIRouter(prefix="/webhooks", tags=["Order Feature"])


@router.post("/{business_id}/orders/{order_id}", response_model=GenericResponse[None])
@rest_endpoint
async def create_order(
    business_id: UUID,
    order_id: UUID,
    mediator: Annotated[Mediator, Depends(mediator)],
) -> BaseResponse[None]:
    return await mediator.send(SendWebhookCommand(business_id, order_id))
