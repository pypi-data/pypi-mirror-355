from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncUnitOfWork
from rmediator.decorators import request_handler
from rmediator.types import RequestHandler

from ed_notification.application.common.responses.base_response import \
    BaseResponse
from ed_notification.application.features.notification.dtos.notification_dto import \
    NotificationDto
from ed_notification.application.features.notification.requests.queries import \
    GetNotificationQuery
from ed_notification.common.logging_helpers import get_logger

LOG = get_logger()


@request_handler(GetNotificationQuery, BaseResponse[NotificationDto])
class GetNotificationQueryHandler(RequestHandler):
    def __init__(self, uow: ABCAsyncUnitOfWork):
        self._uow = uow

    async def handle(
        self, request: GetNotificationQuery
    ) -> BaseResponse[NotificationDto]:
        async with self._uow.transaction():
            notification = await self._uow.notification_repository.get(
                id=request.notification_id
            )

            return BaseResponse[NotificationDto].success(
                "Notification fetched successfully",
                NotificationDto(**notification.__dict__),
            )
