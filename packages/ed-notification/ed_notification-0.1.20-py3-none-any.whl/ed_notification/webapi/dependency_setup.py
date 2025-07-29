from typing import Annotated

from ed_domain.persistence.async_repositories import ABCAsyncUnitOfWork
from ed_domain.utils.email.abc_email_sender import ABCEmailSender
from ed_domain.utils.sms.abc_sms_sender import ABCSmsSender
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork
from ed_infrastructure.utils.email.email_sender import EmailSender
from ed_infrastructure.utils.sms.sms_sender import SmsSender
from fastapi import Depends
from rmediator.mediator import Mediator

from ed_notification.application.features.notification.handlers.commands import (
    SendNotificationCommandHandler, UpdateNotificationCommandHandler)
from ed_notification.application.features.notification.handlers.queries import (
    GetNotificationQueryHandler, GetNotificationsQueryHandler)
from ed_notification.application.features.notification.requests.commands import (
    SendNotificationCommand, UpdateNotificationCommand)
from ed_notification.application.features.notification.requests.queries import (
    GetNotificationQuery, GetNotificationsQuery)
from ed_notification.common.generic_helpers import get_config
from ed_notification.common.typing.config import Config


def email_sender(config: Annotated[Config, Depends(get_config)]) -> ABCEmailSender:
    return EmailSender(config["resend"]["api_key"])


def sms_sender(config: Annotated[Config, Depends(get_config)]) -> ABCSmsSender:
    return SmsSender(config["infobig_key"])


def unit_of_work(
    config: Annotated[Config, Depends(get_config)],
) -> ABCAsyncUnitOfWork:
    return UnitOfWork(config["db"])


def get_mediator(
    config: Annotated[Config, Depends(get_config)],
    uow: Annotated[ABCAsyncUnitOfWork, Depends(unit_of_work)],
    email_sender: Annotated[ABCEmailSender, Depends(email_sender)],
    sms_sender: Annotated[ABCSmsSender, Depends(sms_sender)],
) -> Mediator:
    # Setup
    mediator = Mediator()

    requests_and_handlers = [
        (
            SendNotificationCommand,
            SendNotificationCommandHandler(
                config, uow, email_sender, sms_sender),
        ),
        (
            UpdateNotificationCommand,
            UpdateNotificationCommandHandler(uow),
        ),
        (GetNotificationQuery, GetNotificationQueryHandler(uow)),
        (GetNotificationsQuery, GetNotificationsQueryHandler(uow)),
    ]

    for request, handler in requests_and_handlers:
        mediator.register_handler(request, handler)

    return mediator
