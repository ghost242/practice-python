import datetime
import logging
from collections import OrderedDict
from operator import itemgetter
from typing import Dict, Tuple
from urllib.parse import urlparse, urlunparse

import pytz
import typing

from .sign_process import (
    __configure,
    canonical_querystring,
    conf_aws,
    const,
    credential_scope,
    sign_task_1,
    sign_task_2,
    sign_task_3,
    sign_task_4,
)

__all__ = ["create_sign", "aws_ns"]


aws_ns = {
    "sqs_ns": "http://queue.amazonaws.com/doc/2012-11-05/",
    "s3_ns": "http://s3.amazonaws.com/doc/2006-03-01/",
    "sns_ns": "http://sns.amazonaws.com/doc/2010-03-31/",
}


def config_credentials(
    access_key: typing.Text = None,
    secret_key: typing.Text = None,
    session_token: typing.Text = None,
    region: typing.Text = None,
):
    __configure(
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        region=region,
    )


def create_sign(
    service_name,
    action,
    version,
    *,
    region: str = None,
    req_method: str,
    service_header: dict = None,
    service_query: dict = None,
    req_payload="",
    **kwargs,
) -> Tuple[Dict[str, str], str]:
    """
    Create AWS REST API authorization signature

    :param service_name: AWS Service name(e.g. sqs, s3, athena)
    :param action: User want action in service. It must get exact name in this
        documentation. (e.g. for sqs, https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_Operations.html)
    :param version: document version for service protocol
    :param region: For want service area about AWS.
    :param req_method: User want request method.
    :param service_header: additional header set for service
    :param service_query: additional query set for service.
    :param req_payload:
    :param kwargs: extra arguments(e.g. bucket name(s3), key(s3))
    :return: HTTP Headers, URL path for send request payload.
    :rtype: Tuple[Dict[str, str], str]
    """
    timestamp = datetime.datetime.now(tz=pytz.timezone("UTC"))
    amz_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = amz_date[0:8]

    if region is None:
        region = conf_aws.get("__region__")

    req_method = req_method.upper()
    if req_method == "GET":
        req_payload = ""

    host = const.get("__base_domain__").format(
        service=service_name, region=region
    )
    path = "/"

    default_header = {
        "Host": host,
        "X-Amz-Date": amz_date,
    }
    if service_header:
        default_header.update(service_header)

    if "__token__" in conf_aws and conf_aws["__token__"]:
        default_header["X-Amz-Security-Token"] = conf_aws["__token__"]

    default_header = OrderedDict(
        sorted(
            [(i.lower(), j) for i, j in default_header.items()],
            key=itemgetter(0),
        )
    )

    if service_name == "s3":
        if "bucket" not in kwargs:
            raise Exception(
                "In s3 service, bucket name must set in keyword arguments."
            )
        path_src = [kwargs.get("bucket")]
        if "key" in kwargs:
            path_src.append(kwargs.get("key"))
        # path_src = [kwargs.get("bucket"), kwargs.get("key")]
        path = "/" + "/".join(path_src)

        if (
            "x-amz-content-sha256" in default_header
            or "X-Amz-Content-Sha256" in default_header
        ):
            req_payload = default_header["x-amz-content-sha256"]
    elif service_name == "sqs" and "QueueUrl" in service_query:
        queue_url = urlparse(service_query["QueueUrl"])
        path = queue_url.path

        del service_query["QueueUrl"]

    default_query = {
        "Action": action,
        "Version": version,
        "X-Amz-Date": amz_date,
    }
    if service_query:
        default_query.update(service_query)
    default_query = OrderedDict(
        sorted(
            [(i, j) for i, j in default_query.items()],
            key=itemgetter(0),
        )
    )

    logging.debug(conf_aws)

    canonical_request = sign_task_1(
        req_method, path, default_header, default_query, req_payload
    )
    string_to_sign = sign_task_2(
        service_name, region, amz_date, date_stamp, canonical_request
    )
    signature = sign_task_3(
        conf_aws.get("__secret_key__"),
        date_stamp,
        region,
        service_name,
        string_to_sign,
    )
    headers = sign_task_4(
        const.get("__algorithm__"),
        conf_aws.get("__access_key__"),
        credential_scope(date_stamp, region, service_name),
        signature,
        **default_header,
    )

    if logging.getLogger().level == logging.DEBUG:
        print("canonical_request", "=" * 10, "\n", canonical_request)
        print("string_to_sign", "=" * 10, "\n", string_to_sign)
        print("signature", "=" * 10, "\n", signature)
        print("headers", "=" * 10, "\n", headers)
        print(
            "query string",
            "=" * 10,
            "\n",
            canonical_querystring(default_query),
        )

    if req_method.upper() == "POST":
        cqs = ""
    else:
        cqs = canonical_querystring(default_query)
    request_url = urlunparse(
        (
            const.get("__scheme__"),  # scheme
            host,  # domain name
            path,  # path
            "",  # params
            cqs,  # query string
            "",  # fragment
        )
    )
    return headers, request_url
