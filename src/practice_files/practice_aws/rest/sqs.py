import logging

import boto3
import requests

from signing import create_sign


def get_msg(user_id, queue_name):
    sqs_resource = boto3.resource(
        "sqs",
    )
    queue = sqs_resource.Queue(
        f"https://sqs.ap-northeast-2.amazonaws.com/{user_id}/{queue_name}"
    )

    msg = queue.receive_messages(MaxNumberOfMessages=5)
    print(len(msg))
    for m in msg:
        print(m.body)
        m.delete()

    return msg


def receive_message(queue_url, message_nums=1, receive_options="All"):
    query_string = {
        "QueueUrl": queue_url,
        "MaxNumberOfMessages": message_nums,
        "AttributeName": receive_options,
    }

    headers, request_url = create_sign(
        "sqs",
        "ReceiveMessage",
        "2012-11-05",
        service_query=query_string,
        req_method="get",
    )

    r = requests.get(
        request_url, headers=headers
    )  # result_header from sign_task_4

    logging.debug("Response code: %d\n" % r.status_code)
    logging.debug(r.text)
    return r.text


def send_message(queue_url, message):
    query_string = {"MessageBody": message, "QueueUrl": queue_url}

    headers, request_url = create_sign(
        "sqs",
        "SendMessage",
        "2012-11-05",
        service_query=query_string,
        req_method="get",
    )

    r = requests.get(
        request_url, headers=headers
    )  # result_header from sign_task_4

    logging.debug("Response code: %d\n" % r.status_code)

    return r.text


def list_queues(
    queue_name="",
):
    action = "ListQueues"

    if queue_name:
        query = {
            "QueueNamePrefix": queue_name,
        }
    else:
        query = dict()

    headers, request_url = create_sign(
        "sqs", action, "2012-11-05", service_query=query, req_method="get"
    )

    r = requests.get(
        request_url, headers=headers
    )  # result_header from sign_task_4

    logging.debug("Response code: %d\n" % r.status_code)
    logging.debug(r.text)

    return r.text
