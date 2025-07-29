from datetime import UTC, datetime

from ed_domain.common.exceptions import ApplicationException, Exceptions
from ed_domain.core.entities import Notification
from ed_domain.core.entities.notification import NotificationType
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from ed_domain.utils.email.abc_email_sender import ABCEmailSender
from ed_domain.utils.sms.abc_sms_sender import ABCSmsSender
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_notification.application.common.responses.base_response import \
    BaseResponse
from ed_notification.application.features.notification.dtos import \
    NotificationDto
from ed_notification.application.features.notification.requests.commands.send_notification_command import \
    SendNotificationCommand
from ed_notification.common.generic_helpers import get_new_id
from ed_notification.common.logging_helpers import get_logger
from ed_notification.common.typing.config import Config

LOG = get_logger()

DEFAULT_EMAIL_ADDRESS = "default@ed.com"


@request_handler(SendNotificationCommand, BaseResponse[NotificationDto])
class SendNotificationCommandHandler(RequestHandler):
    def __init__(
        self,
        config: Config,
        uow: ABCAsyncUnitOfWork,
        email_sender: ABCEmailSender,
        sms_sender: ABCSmsSender,
    ):
        self._config = config
        self._uow = uow
        self._email_sender = email_sender
        self._sms_sender = sms_sender

    async def handle(
        self, request: SendNotificationCommand
    ) -> BaseResponse[NotificationDto]:
        async with self._uow.transaction():
            dto = request.dto
            user = await self._uow.auth_user_repository.get(id=dto["user_id"])
            print("USER", user)

            if not user:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    "Notification failed.",
                    ["User not found"],
                )

            if not user.email:
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    "Notification failed.",
                    ["User email not found"],
                )

            created_notification = await self._uow.notification_repository.create(
                Notification(
                    id=get_new_id(),
                    user_id=user.id,
                    message=dto["message"],
                    read_status=False,
                    create_datetime=datetime.now(UTC),
                    update_datetime=datetime.now(UTC),
                    notification_type=NotificationType[dto["notification_type"]],
                    deleted=False,
                    deleted_datetime=datetime.now(UTC),
                )
            )

            try:
                if dto["notification_type"] == NotificationType.EMAIL:
                    if user.email == DEFAULT_EMAIL_ADDRESS:
                        LOG.info(
                            "Sending email to default destinations instead.")
                        await self._send_email(
                            self._config["default_email_destination"], dto["message"]
                        )
                    else:
                        await self._send_email(user.email, dto["message"])

            except Exception as e:
                LOG.error(f"Failed to send email: {e}")
                raise ApplicationException(
                    Exceptions.BadRequestException,
                    "Notification failed.",
                    ["Cannot send email."],
                )

        return BaseResponse[NotificationDto].success(
            "Notification sent",
            NotificationDto(**created_notification.__dict__),
        )

    async def _send_email(self, email: str, message: str) -> None:
        return await self._email_sender.send(
            self._config["resend"]["from_email"],
            email,
            "EasyDrop Notification",
            message,
        )
