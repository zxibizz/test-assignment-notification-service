import asyncio
import logging
from collections.abc import Iterable
from contextlib import asynccontextmanager
from enum import Enum

import httpx
from aiolimiter import AsyncLimiter

GLOBAL_RATE_LIMITER = AsyncLimiter(max_rate=10, time_period=1)


class MailingMessageStatus(str, Enum):
    PENDING = "Pending"
    SUCCEED = "Succeed"
    FAILED = "Failed"


class MailingMessage:
    def __init__(self, msg_id: int, phone: str, text: str):
        self.msg_id = msg_id
        self.phone = phone
        self.text = text
        self.status: MailingMessageStatus = MailingMessageStatus.PENDING


class MailingClientApiException(BaseException):
    def __init__(self, http_resp):
        self.status = http_resp.status_code
        self.reason = http_resp.reason_phrase
        self.body = http_resp.content
        self.headers = http_resp.headers

    def __str__(self):
        error_message = (
            "Failed to call a mailing api!\n" f"{self.status}\nReason: {self.reason}\n"
        )
        if self.headers:
            error_message += f"HTTP response headers: {self.headers}\n"
        if self.body:
            error_message += f"HTTP response body: {self.body}\n"
        return error_message


class MailingClient:
    def __init__(self, token: str, rate_limiter: AsyncLimiter = None):
        self._token = token
        self._root_url = "https://probe.fbrq.cloud"
        self._client: httpx.AsyncClient | None = None
        self._rate_limiter: AsyncLimiter = rate_limiter or GLOBAL_RATE_LIMITER

    def _create_client(self):
        headers = {"authorization": f"Bearer {self._token}"}
        return httpx.AsyncClient(
            base_url=self._root_url,
            headers=headers,
            # http2=True,
        )

    @asynccontextmanager
    async def session(self):
        assert (
            self._client is None
        ), "Trying to start a session while there is an active one"

        try:
            self._client = self._create_client()
            yield
        finally:
            if self._client:
                await self._client.aclose()
                self._client = None

    @asynccontextmanager
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client:
            yield self._client
        else:
            temp_client = None
            try:
                temp_client = self._create_client()
                yield temp_client
            finally:
                if temp_client:
                    await temp_client.aclose()

    async def _call_api(self, url: str, json: dict) -> httpx.Response:
        async with self._rate_limiter:
            async with self._get_client() as client:
                response = await client.post(
                    url,
                    json=json,
                )
                return response

    async def _raise_for_exception(
        self, response: httpx.Response, silent: bool = False
    ):
        if response.is_success:
            return

        try:
            raise MailingClientApiException(http_resp=response)
        except MailingClientApiException as e:
            if not silent:
                raise
            logging.warning("Suppressed the mailing client exception", exc_info=e)
            try:
                from sentry import capture_exception

                capture_exception(e)
            except ModuleNotFoundError:
                pass

    async def post_message(self, message: MailingMessage):
        response = await self._call_api(
            f"/v1/send/{message.msg_id}",
            {
                "id": message.msg_id,
                "phone": message.phone,
                "text": message.text,
            },
        )
        await self._raise_for_exception(response, silent=True)
        if response.is_success:
            message.status = MailingMessageStatus.SUCCEED
        else:
            logging.warning("Failed to post a message!")
            message.status = MailingMessageStatus.FAILED

        return message

    async def post_message_batch(self, messages: Iterable[MailingMessage]):
        async with self.session():
            await asyncio.gather(*[self.post_message(message) for message in messages])
