import os
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Header, Request

from jarvis.api.logger import logger
from jarvis.executors import files
from jarvis.modules.exceptions import APIResponse
from jarvis.modules.models import models

router = APIRouter()


@router.post(path="/secure-send")
async def secure_send_api(request: Request, access_token: Optional[str] = Header(None)):
    """API endpoint to share/retrieve secrets.

    Args:
        request: FastAPI request module.
        access_token: Access token for the secret to be retrieved.

    Raises:

        - 200: For a successful authentication (secret will be returned)
        - 400: For a bad request if headers are passed with underscore
        - 401: For a failed authentication (if the access token doesn't match)
        - 404: If the ``secure_send`` mapping file is unavailable
    """
    logger.info(
        "Connection received from %s via %s using %s",
        request.client.host,
        request.headers.get("host"),
        request.headers.get("user-agent"),
    )
    key = access_token or request.headers.get("access-token")
    if not key:
        logger.warning("'access-token' not received in headers")
        raise APIResponse(
            status_code=HTTPStatus.UNAUTHORIZED.real,
            detail=HTTPStatus.UNAUTHORIZED.phrase,
        )
    if key.startswith("\\"):
        key = bytes(key, "utf-8").decode(encoding="unicode_escape")
    if os.path.isfile(models.fileio.secure_send):
        secure_strings = files.get_secure_send()
        if secret := secure_strings.get(key):
            logger.info("secret was accessed using secure token, deleting secret")
            files.delete_secure_send(key)
            raise APIResponse(status_code=HTTPStatus.OK.real, detail=secret)
        else:
            logger.info(
                "secret access was denied for key: %s, available keys: %s",
                key,
                [*secure_strings.keys()],
            )
            raise APIResponse(
                status_code=HTTPStatus.UNAUTHORIZED.real,
                detail=HTTPStatus.UNAUTHORIZED.phrase,
            )
    else:
        logger.info("'%s' not found", models.fileio.secure_send)
        raise APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase
        )
