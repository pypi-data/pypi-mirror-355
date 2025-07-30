from dataclasses import dataclass
from uuid import UUID

from rmediator.decorators import request
from rmediator.mediator import Request

from ed_webhook.application.common.responses.base_response import BaseResponse


@request(BaseResponse[None])
@dataclass
class SendWebhookCommand(Request):
    business_id: UUID
    order_id: UUID
