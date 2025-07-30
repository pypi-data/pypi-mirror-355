import json
from collections.abc import Iterable
from os import getenv
from typing import Any, cast
from uuid import uuid4

import boto3
from boto3.resources.base import ServiceResource
from extratools_core.crudl import CRUDLDict
from extratools_core.json import JsonDict
from toolz.itertoolz import partition_all

from .helpers import ClientErrorHandler

STAGE: str = getenv("STAGE", "local")


default_service_resource: ServiceResource = boto3.resource(
    "sqs",
    endpoint_url=(
        "http://localhost:4566" if STAGE == "local"
        else None
    ),
)

type Queue = Any

FIFO_QUEUE_NAME_SUFFIX = ".fifo"


def get_resource_dict(
    *,
    service_resource: ServiceResource | None = None,
    queue_name_prefix: str | None = None,
) -> CRUDLDict[str, Queue]:
    service_resource = service_resource or default_service_resource

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/service-resource/index.html

    def check_queue_name(queue_name: str) -> None:
        if queue_name_prefix and not queue_name.startswith(queue_name_prefix):
            raise ValueError

    def create_func(queue_name: str | None, attributes: dict[str, str]) -> None:
        if queue_name is None:
            raise ValueError

        check_queue_name(queue_name)

        service_resource.create_queue(
            QueueName=queue_name,
            Attributes={
                "FifoQueue": str(queue_name.endswith(FIFO_QUEUE_NAME_SUFFIX)).lower(),
                **attributes,
            },
        )

    @ClientErrorHandler(
        "QueueDoesNotExist",
        KeyError,
    )
    def read_func(queue_name: str) -> Queue:
        check_queue_name(queue_name)

        return service_resource.get_queue_by_name(
            QueueName=queue_name,
        )

    def update_func(queue_name: str, attributes: dict[str, str]) -> None:
        check_queue_name(queue_name)

        service_resource.get_queue_by_name(
            QueueName=queue_name,
        ).set_attributes(
            Attributes={
                **attributes,
            },
        )

    def delete_func(queue_name: str) -> None:
        check_queue_name(queue_name)

        service_resource.get_queue_by_name(
            QueueName=queue_name,
        ).delete()

    def list_func(_: None) -> Iterable[tuple[str, Queue]]:
        for queue in (
            service_resource.queues.filter(
                QueueNamePrefix=queue_name_prefix,
            )
            if queue_name_prefix
            else service_resource.queues.all()
        ):
            queue_name = cast("str", queue.url).rsplit('/', maxsplit=1)[-1]
            yield queue_name, queue

    return CRUDLDict[str, Queue](
        create_func=create_func,
        read_func=read_func,
        update_func=update_func,
        delete_func=delete_func,
        list_func=list_func,
    )


MESSAGE_BATCH_SIZE = 10


def send_messages(
    queue: Queue,
    messages: Iterable[JsonDict],
    group: str | None = None,
) -> Iterable[JsonDict]:
    batch_id = str(uuid4())

    fifo: bool = queue.url.endswith(FIFO_QUEUE_NAME_SUFFIX)
    if fifo and not group:
        raise ValueError

    for message_batch in partition_all(
        MESSAGE_BATCH_SIZE,
        (
            (f"{batch_id}_{i}", message_data)
            for i, message_data in enumerate(messages)
        ),
    ):
        response: JsonDict = queue.send_messages(Entries=[
            dict(
                Id=message_id,
                MessageBody=json.dumps(message_data),
            ) | (
                dict(
                    MessageDeduplicationId=message_id,
                    MessageGroupId=group,
                )
                if fifo else {}
            )
            for message_id, message_data in message_batch
        ])

        yield from response.get("Successful", [])
        yield from response.get("Failed", [])


class FifoRouter:
    def __init__(
        self,
        *,
        service_resource: ServiceResource | None = None,
        queue_name_prefix: str,
        default_queue_base_name: str,
    ) -> None:
        self.__resource_dict: CRUDLDict[str, Queue] = get_resource_dict(
            service_resource=service_resource,
            queue_name_prefix=queue_name_prefix,
        )

        self.__default_queue: Queue = self.__resource_dict[
            queue_name_prefix + default_queue_base_name + FIFO_QUEUE_NAME_SUFFIX
        ]

        self.__queue_name_prefix = queue_name_prefix

        queue_name_prefix_len = len(queue_name_prefix)
        queue_name_suffix_len = len(FIFO_QUEUE_NAME_SUFFIX)
        self.__queues: dict[str, Queue] = {
            (queue_name[queue_name_prefix_len:])[:-queue_name_suffix_len]: queue
            for queue_name, queue in self.__resource_dict.items()
        }

    def register_queue(
        self,
        queue_base_name: str,
        groups: Iterable[str] | None = None,
        *,
        create: bool = True,
    ) -> None:
        queue_name = self.__queue_name_prefix + queue_base_name + FIFO_QUEUE_NAME_SUFFIX

        if queue_name not in self.__resource_dict:
            if create:
                self.__resource_dict[queue_name] = {}
            else:
                raise KeyError

        queue = self.__resource_dict[queue_name]
        self.__queues.update(dict.fromkeys(groups or [queue_base_name], queue))

    def send_messages(
        self,
        messages: Iterable[JsonDict],
        group: str,
    ) -> Iterable[JsonDict]:
        yield from send_messages(
            self.__queues.get(group, self.__default_queue),
            messages,
            group,
        )
