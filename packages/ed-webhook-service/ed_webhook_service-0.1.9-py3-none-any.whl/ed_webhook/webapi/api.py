import uvicorn
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from ed_webhook.common.exception_helpers import ApplicationException
from ed_webhook.common.logging_helpers import get_logger
from ed_webhook.webapi.common.helpers import GenericResponse
from ed_webhook.webapi.controllers import webhook_controller

LOG = get_logger()


class API(FastAPI):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def start(self) -> None:
        LOG.info("Starting api...")
        self._include_routers()
        self._contain_exceptions()

        uvicorn.run(self, host="0.0.0.0", port=8000)

    def stop(self) -> None:
        LOG.info("API does not need to be stopped...")

    def _include_routers(self) -> None:
        LOG.info("Including routers...")
        self.include_router(webhook_controller.router)

    def _contain_exceptions(self) -> None:
        @self.exception_handler(ApplicationException)
        async def application_exception_handler(
            request: Request, exception: ApplicationException
        ) -> JSONResponse:
            return JSONResponse(
                status_code=exception.error_code,
                content=GenericResponse(
                    is_success=False,
                    message=exception.message,
                    errors=exception.errors,
                    data=None,
                ).to_dict(),
            )
