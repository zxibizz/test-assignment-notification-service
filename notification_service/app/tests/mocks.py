from notification_service.utils.mailing_client import (
    MailingMessage,
    MailingMessageStatus,
)


class TestMailingClient:
    posted_messages = []

    async def post_message(self, message: MailingMessage):
        message.status = MailingMessageStatus.SUCCEED
        self.posted_messages.append(message)

    async def post_message_batch(self, messages: list[MailingMessage]):
        for msg in messages:
            await self.post_message(msg)
