from ed_domain.common.logging import get_logger
from ed_infrastructure.documentation.message_queue.rabbitmq.rabbitmq_multiple_queue_producers import \
    RabbitMQMultipleQueuesProducer

from ed_notification.application.features.notification.dtos.send_notification_dto import \
    SendNotificationDto
from ed_notification.documentation.message_queue.rabbitmq.abc_notification_rabbitmq_subscriber import (
    ABCNotificationRabbitMQSubscriber, NotificationQueues)
from ed_notification.documentation.message_queue.rabbitmq.notification_queue_descriptions import \
    NotificationQueueDescriptions

LOG = get_logger()


class NotificationRabbitMQSubscriber(ABCNotificationRabbitMQSubscriber):
    def __init__(self, connection_url: str) -> None:
        self._connection_url = connection_url
        descriptions = NotificationQueueDescriptions(
            connection_url).descriptions

        all_queue_names = [
            desc["connection_parameters"]["queue"]
            for desc in descriptions
            if "request_model" in desc
        ]

        producer_request_model = SendNotificationDto
        for desc in descriptions:
            if "request_model" in desc:
                producer_request_model = desc["request_model"]
                break

        if all_queue_names:
            producer_url = descriptions[0]["connection_parameters"]["url"]
            self._main_producer = RabbitMQMultipleQueuesProducer[
                producer_request_model
            ](url=producer_url, queues=all_queue_names)

        else:
            LOG.warning(
                "No producer-related queue descriptions found. No main producer initialized."
            )
            self._main_producer = None

    async def start(self) -> None:
        LOG.info("Starting RabbitMQ producer...")
        if self._main_producer:
            try:
                await self._main_producer.start()
                LOG.info(
                    f"Main producer started and declared queues: {self._main_producer._queues}"
                )
            except Exception as e:
                LOG.error(f"Failed to start main producer: {e}")
                raise
        else:
            LOG.info("No main producer to start.")

    async def send_notification(
        self,
        send_notification_dto: SendNotificationDto,
    ) -> None:
        if not self._main_producer:
            LOG.error(
                "Main producer is not initialized. Cannot send notification.")
            raise RuntimeError("RabbitMQ producer not available.")

        queue_name = NotificationQueues.SEND_NOTIFICATION

        LOG.info(
            f"Publishing to queue: {queue_name} the message: {send_notification_dto}"
        )
        await self._main_producer.publish(send_notification_dto, queue_name)

    async def stop(self) -> None:
        LOG.info("Stopping RabbitMQ producer...")
        if self._main_producer:
            self._main_producer.stop()
        else:
            LOG.info("No main producer to stop.")
