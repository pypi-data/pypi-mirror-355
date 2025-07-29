from datetime import UTC, datetime

from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_notification.application.common.responses.base_response import \
    BaseResponse
from ed_notification.application.features.notification.dtos import (
    NotificationDto, UpdateNotificationDto)
from ed_notification.application.features.notification.requests.commands import \
    UpdateNotificationCommand
from ed_notification.common.logging_helpers import get_logger

LOG = get_logger()


@request_handler(UpdateNotificationCommand, BaseResponse[NotificationDto])
class UpdateNotificationCommandHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

    async def handle(
        self, request: UpdateNotificationCommand
    ) -> BaseResponse[NotificationDto]:
        async with self._uow.transaction():
            notification_id = request.notification_id
            dto: UpdateNotificationDto = request.dto

            if notification := await self._uow.notification_repository.get(
                id=notification_id
            ):
                notification.read_status = dto["read_status"]
                notification.update_datetime = datetime.now(UTC)
                updated = await self._uow.notification_repository.update(
                    notification_id, notification
                )

                if updated:
                    return BaseResponse[NotificationDto].success(
                        "Notification updated successfully.",
                        NotificationDto(**notification.__dict__),
                    )

                return BaseResponse[NotificationDto].error(
                    "Notification not updated.",
                    ["Notification cannot be updated with the given data."],
                )

            return BaseResponse[NotificationDto].error(
                "Notification not updated.",
                [f"Notification with id = {notification_id} not found."],
            )
