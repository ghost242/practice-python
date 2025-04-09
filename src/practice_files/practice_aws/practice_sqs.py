import json
import logging
from datetime import datetime

import boto3

from signing import config_credentials


def receive():
    sqs = boto3.resource(
        "sqs",
        region_name="ap-northeast-2",
    )
    queue = sqs.Queue("")


def send_message(url, msg):
    sqs = boto3.resource(
        "sqs",
        region_name="ap-northeast-2",
    )
    queue = sqs.Queue(url)

    res = queue.send_message(MessageBody=msg)

    print(res)

def main():
    # send_message_job_queue()
    # logging.getLogger().setLevel(logging.DEBUG)
    # config_credentials(region="ap-northeast-2",)
    # queues = list_queues()
    # print(queues)

    for i in range(20):
        res = send_message(
            "https://sqs.ap-northeast-2.amazonaws.com/{account_id}/TestTriggerQueue",
            f"New test message {i}",
        )
        print(res)
    # receive()
    # ps = []
    # for i in range(10):
    #     p = Process(target=receive)
    #
    #     p.start()
    #     ps.append(p)
    #
    # for p in ps:
    #     p.join()


if __name__ == "__main__":
    main()
