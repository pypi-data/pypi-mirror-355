from typing import Annotated

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork
from fastapi import Depends
from rmediator.mediator import Mediator

from ed_webhook.application.features.webhook.handlers.commands import \
    SendWebhookCommandHandler
from ed_webhook.application.features.webhook.requests.commands import \
    SendWebhookCommand
from ed_webhook.common.generic_helpers import get_config
from ed_webhook.common.typing.config import Config


def get_uow(config: Annotated[Config, Depends(get_config)]) -> ABCAsyncUnitOfWork:
    return UnitOfWork(config["db"])


def mediator(
    uow: Annotated[ABCAsyncUnitOfWork, Depends(get_uow)],
) -> Mediator:
    mediator = Mediator()

    handlers = [
        (
            SendWebhookCommand,
            SendWebhookCommandHandler(uow),
        ),
    ]
    for command, handler in handlers:
        mediator.register_handler(command, handler)

    return mediator
