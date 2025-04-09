import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Sequence, Tuple, Optional, Literal 
from warnings import warn

import requests

from ..signing import create_sign

__version__ = "2014-03-28"


# TODO: 모든 함수 안에서 HTTP status code의 에러 값에 대한 처리 로직이 필요함.


RetentionDays = Literal[-1, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]

@dataclass
class LogGroup:
    arn: Optional[str] = field(default=None)
    creationTime: Optional[int] = field(default=None)
    kmsKeyId: Optional[str] = field(default=None)
    logGroupName: Optional[str] = field(default=None)
    metricFilterCount: Optional[int] = field(default=None)
    retentionInDays: Optional[int] = field(default=None)
    storedBytes: Optional[int] = field(default=None)


@dataclass
class LogStream:
    arn: Optional[str] = field(default=None)
    creationTime: Optional[int] = field(default=None)
    firstEventTimestamp: Optional[int] = field(default=None)
    lastEventTimestamp: Optional[int] = field(default=None)
    lastIngestionTime: Optional[int] = field(default=None)
    logStreamName: Optional[str] = field(default=None)
    storedBytes: Optional[int] = field(default=None)
    uploadSequenceToken: Optional[str] = field(default=None)


@dataclass
class LogMessage:
    timestamp: Optional[int] = field(default=None)
    message: Optional[str] = field(default=None)


def describe_log_groups(name_prefix="") -> Sequence[LogGroup]:
    action = "DescribeLogGroups"
    params = dict()
    if name_prefix:
        params = dict(
            logGroupNamePrefix=name_prefix,
        )

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)

    """
    HTTP Status Code: 400

    InvalidParameterException
        A parameter is specified incorrectly.

    HTTP Status Code: 500

    ServiceUnavailableException
        The service cannot complete the request.

    """

    if 200 <= res.status_code < 300:
        resp_body = res.json()
        groups = resp_body.get("logGroups")

        return list(map(lambda i: LogGroup(**i), groups))
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")


def create_log_group(name, tags: Optional[dict] = None) -> str:
    action = "CreateLogGroup"
    params = dict(
        logGroupName=name,
    )
    if tags:
        params["tags"] = tags

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)
    """

    HTTP Status Code: 400

    InvalidParameterException
        A parameter is specified incorrectly.

    LimitExceededException
        You have reached the maximum number of resources that can be created.

    OperationAbortedException
        Multiple requests to update the same resource were in conflict.

    ResourceAlreadyExistsException
        The specified resource already exists.

    HTTP Status Code: 500

    ServiceUnavailableException
        The service cannot complete the request.

    """
    if 200 <= res.status_code < 300:
        return name
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")


def put_retention_policy(
    log_group: str, retention_option: RetentionDays = -1
) -> Tuple[str, int]:
    action = "PutRetentionPolicy"
    params = dict(
        logGroupName=log_group,
    )
    if retention_option:
        params["retentionInDays"] = retention_option
    else:
        warn(f"{retention_option} is not acceptable value.", ResourceWarning)

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)

    """

    HTTP Status Code: 400

    InvalidParameterException
        A parameter is specified incorrectly.

    OperationAbortedException
        Multiple requests to update the same resource were in conflict.

    ResourceNotFoundException
        The specified resource does not exist.

    HTTP Status Code: 500

    ServiceUnavailableException
        The service cannot complete the request.

    """

    if 200 <= res.status_code < 300:
        return log_group, retention_option
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")


def describe_log_streams(log_group, name_prefix="") -> Sequence[LogStream]:
    action = "DescribeLogStreams"
    params = dict(
        logGroupName=log_group,
    )
    if name_prefix:
        params["logStreamNamePrefix"] = name_prefix

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)
    """

    HTTP Status Code: 400

    InvalidParameterException
        A parameter is specified incorrectly.

    ResourceNotFoundException
        The specified resource does not exist.

    HTTP Status Code: 500

    ServiceUnavailableException
        The service cannot complete the request.

    """

    if 200 <= res.status_code < 300:
        resp_body = res.json()
        streams = resp_body.get("logStreams")

        return list(map(lambda i: LogStream(**i), streams))
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")


def create_log_stream(log_group, name) -> str:
    action = "CreateLogStream"
    params = dict(logGroupName=log_group, logStreamName=name)

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)
    """

    HTTP Status Code: 400

    InvalidParameterException
        A parameter is specified incorrectly.

    ResourceAlreadyExistsException
        The specified resource already exists.

    ResourceNotFoundException
        The specified resource does not exist.

    HTTP Status Code: 500

    ServiceUnavailableException
        The service cannot complete the request.

    """

    if 200 <= res.status_code < 300:
        return name
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")


def put_log_events(
    log_group,
    log_stream,
    event_messages: Sequence[LogMessage],
    sequence_token="",
) -> str:
    action = "PutLogEvents"

    params = dict(
        logEvents=list(map(asdict, event_messages)),
        logGroupName=log_group,
        logStreamName=log_stream,
    )

    if sequence_token:
        params["sequenceToken"] = sequence_token

    payload = json.dumps(params)

    header = {
        "content-length": str(len(payload)),
        "content-type": "application/x-amz-json-1.1",
        "connection": "Keep-Alive",
        "x-amz-target": f"Logs_{__version__.replace('-', '')}.{action}",
    }
    header, url = create_sign(
        "logs",
        action,
        __version__,
        req_method="post",
        service_header=header,
        req_payload=payload,
    )

    res = requests.post(url, headers=header, data=payload)

    """

    DataAlreadyAcceptedException

        The event was already logged.

        HTTP Status Code: 400
    InvalidParameterException

        A parameter is specified incorrectly.

        HTTP Status Code: 400
    InvalidSequenceTokenException

        The sequence token is not valid. You can get the correct sequence token
        in the expectedSequenceToken field
        in the InvalidSequenceTokenException message.

        HTTP Status Code: 400
    ResourceNotFoundException

        The specified resource does not exist.

        HTTP Status Code: 400
    ServiceUnavailableException

        The service cannot complete the request.

        HTTP Status Code: 500
    UnrecognizedClientException

        The most likely cause is an invalid AWS access key ID or secret key.

        HTTP Status Code: 400

    """

    if 200 <= res.status_code < 300:
        resp_body = res.json()
        next_sequence_token = resp_body.get("nextSequenceToken")
        rejected_log_info = resp_body.get("rejectedLogEventsInfo")

        return next_sequence_token
    else:
        raise Exception(f"{res.status_code}:{res.reason}:{res.content}")
