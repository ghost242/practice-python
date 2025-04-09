import logging
import time
from uuid import uuid4

import boto3

from ..rest import cloudwatch_logs
from ..rest.cloudwatch_logs import LogMessage
from ..signing import config_credentials


def remove_floating_point_from_num(n):
    return int(n * (10 ** len(str(n).split(".")[1])))


def empty_group():
    res = cloudwatch_logs.describe_log_groups(name_prefix="unknown")

    print(res)


def exists_group():
    res = cloudwatch_logs.describe_log_groups()

    print(res)


def send_log_in_group():
    group_name = "test_new_loggroup"
    stream_name = "test_new_loggroup/test_any_stream"

    if not cloudwatch_logs.describe_log_groups(group_name):
        cloudwatch_logs.create_log_group(name=group_name)
    if not cloudwatch_logs.describe_log_streams(group_name, stream_name):
        cloudwatch_logs.create_log_stream(
            log_group=group_name, name=stream_name
        )

    res = cloudwatch_logs.put_log_events(
        log_group=group_name,
        log_stream=stream_name,
        event_messages=[
            LogMessage(
                int(round(time.time() * 1000)), "this is 1 test message"
            ),
            LogMessage(
                int(round(time.time() * 1000)), "this is 2 test message"
            ),
            LogMessage(
                int(round(time.time() * 1000)), "this is 3 test message"
            ),
            LogMessage(
                int(round(time.time() * 1000)), "this is 4 test message"
            ),
            LogMessage(
                int(round(time.time() * 1000)), "this is 5 test message"
            ),
            LogMessage(
                int(round(time.time() * 1000)), "this is 6 test message"
            ),
        ],
    )
    print(res)


def get_log_in_stream():
    group_name = "test_new_loggroup"
    stream_name = "test_new_loggroup/test_any_stream"

    res = cloudwatch_logs.get_log_events(group_name, stream_name)

    print(res)


def main():
    config_credentials(None, None, None, "ap-northeast-2")
    send_log_in_group()
    #
    # get_log_in_stream()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)

    logging.debug("Hello")
    main()
