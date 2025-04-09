import hashlib
import hmac
import json
import logging
import os
import typing
from collections import OrderedDict
from functools import wraps
from urllib.parse import quote

import requests

conf_aws = dict(
    __region__="ap-northeast-2",
    __access_key__=os.environ.get("AWS_ACCESS_KEY_ID"),
    __secret_key__=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    __token__="",
    __token_expiration__="",
)

const = dict(
    __scheme__="https",
    __base_domain__="{service}.{region}.amazonaws.com",
    __algorithm__="AWS4-HMAC-SHA256",
)


def __get_from_credential_file(file_name):
    import configparser

    conf = configparser.ConfigParser()
    conf.read(file_name)

    if "default" not in conf:
        raise Exception("Not exists default credential info")

    api_access_key = conf["default"]["aws_access_key_id"]
    api_secret_key = conf["default"]["aws_secret_access_key"]
    api_region = conf["default"]["region"]

    return api_access_key, api_secret_key, api_region


def __get_from_container():
    res = requests.get(
        f"http://169.254.170.2{os.getenv('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI')}"
    )
    if res.status_code < 400:
        credential_info = res.json()
        api_access_key = credential_info["AccessKeyId"]
        api_secret_key = credential_info["SecretAccessKey"]
        api_session_token = credential_info["Token"]
    else:
        raise Exception("Fail to get credential info.")
    return api_access_key, api_secret_key, api_session_token


def __get_from_ec2():
    # as EC2
    with open("/sys/hypervisor/uuid") as fd:
        system_id = fd.read()

    if system_id.startswith("ec2"):

        def get_token():
            header_ = {
                "X-aws-ec2-metadata-token-ttl-seconds": "21600",
            }
            url_ = "http://169.254.169.254/latest/api/token"

            res_ = requests.put(url_, headers=header_)

            if res_.status_code < 400:
                token = res_.text
                return token
            else:
                raise Exception("Fail to get region info.")

        def get_region(token):
            header_ = {"X-aws-ec2-metadata-token": token}
            url_ = "http://169.254.169.254/latest/dynamic/instance-identity/document"
            res_ = requests.get(url_, headers=header_)
            if res_.status_code < 400:
                metainfo = res_.json()

                return metainfo.get("region")
            else:
                raise Exception("Fail to get region info.")

        def get_role(token):
            header_ = {"X-aws-ec2-metadata-token": token}
            url_ = "http://169.254.169.254/latest/meta-data/iam/security-credentials"
            res_ = requests.get(url_, headers=header_)

            if res_.status_code < 400:
                return res_.text
            else:
                raise Exception("Fail to get role name.")

        def get_keys(role_name, token):
            header = {"X-aws-ec2-metadata-token": token}
            url = (
                "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
                + role_name
            )
            res_ = requests.get(url, headers=header)

            if res_.status_code < 400:
                role_info = res_.json()
                return (
                    role_info.get("AccessKeyId"),
                    role_info.get("SecretAccessKey"),
                    role_info.get("Token"),
                    role_info.get("Expiration"),
                )
            else:
                raise Exception("Fail to get credential info.")

        request_token = get_token()

        access_info = get_keys(get_role(request_token), request_token)
        api_region = get_region(request_token)
        api_access_key = access_info[0]
        api_secret_key = access_info[1]
        api_session_token = access_info[2]

        return api_access_key, api_secret_key, api_region, api_session_token


def __get_from_lambda():
    pass


def get_aws_acc_info():
    """
    Priority -> parameter -> credential file -> ecs container -> ec2 instance -> lambda instance

    :return:
    """
    # get uuid for ec2 environment; It is very sensitive way by AWS EC2 configuration.
    import requests

    api_region = "ap-northeast-2"
    api_access_key = ""
    api_secret_key = ""
    api_session_token = ""

    if os.path.exists(f"{os.getenv('HOME')}/.aws/config") or os.path.exists(
        f"{os.getenv('HOME')}/.aws/credentials"
    ):
        try:
            (
                api_access_key,
                api_secret_key,
                api_region,
            ) = __get_from_credential_file(f"{os.getenv('HOME')}/.aws/config")
        except Exception:
            try:
                (
                    api_access_key,
                    api_secret_key,
                    api_region,
                ) = __get_from_credential_file(
                    f"{os.getenv('HOME')}/.aws/credentials"
                )
            except Exception as e:
                raise e
    elif "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI" in os.environ:
        # as ECS Container
        (
            api_access_key,
            api_secret_key,
            api_region,
            api_session_token,
        ) = __get_from_container()
    elif os.path.exists("/sys/hypervisor/uuid") and os.path.isfile(
        "/sys/hypervisor/uuid"
    ):
        (
            api_access_key,
            api_secret_key,
            api_region,
            api_session_token,
        ) = __get_from_ec2()
    elif {
        "AWS_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
    }.issubset(set(os.environ.keys())):
        # as Lambda or common aws computer
        api_region = os.getenv("AWS_REGION", "")
        api_access_key = os.getenv("AWS_ACCESS_KEY_ID", "")
        api_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        api_session_token = os.getenv("AWS_SESSION_TOKEN", "")
    else:
        raise Exception(
            "Not supported environment. "
            "May It need to set parameters(access_key, secret_key, "
            "session_token, region) manually."
        )

    return (
        api_region,
        api_access_key,
        api_secret_key,
        api_session_token,
    )


def __configure(
    *,
    access_key: typing.Text = None,
    secret_key: typing.Text = None,
    session_token: typing.Text = None,
    region: typing.Text = None,
) -> typing.NoReturn:
    if not all([access_key, secret_key, region]):
        region, access_key, secret_key, session_token = get_aws_acc_info()

    if region:
        conf_aws["__region__"] = region
    if session_token:
        conf_aws["__token__"] = session_token
    if access_key:
        conf_aws["__access_key__"] = access_key
    if secret_key:
        conf_aws["__secret_key__"] = secret_key

    return conf_aws


# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(key, date_stamp, region_name, service_name):
    logging.debug(f"{key}\n{date_stamp}\n{region_name}\n{service_name}")
    k_date = sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = sign(k_date, region_name)
    k_service = sign(k_region, service_name)
    k_signing = sign(k_service, "aws4_request")
    return k_signing


def single_cache(f):
    cache = list()

    def find_key(k):
        for c in cache:
            if c[0] == k:
                return c
        else:
            return None

    @wraps(f)
    def f_(*args):
        nonlocal cache

        item = find_key(args)
        if not item:
            if isinstance(args, dict) or isinstance(args, OrderedDict):
                key = ((k, v) for k, v in args.items())
            else:
                key = args
            item = (key, f(*args))
            cache.append(item)
            # cache.sort(key=lambda i: i[0])
        return item[1]

    return f_


@single_cache
def credential_scope(
    date_stamp: typing.Text, region: typing.Text, service: typing.Text
):
    return f"{date_stamp}/{region}/{service}/aws4_request"


@single_cache
def canonical_querystring(querystring: typing.Dict):
    _qs = dict()
    for k, v in querystring.items():
        if type(v) in [str, int, float]:
            _qs[k] = str(v)
        elif type(v) in [list, tuple, set, dict]:
            _qs[k] = json.dumps(v)
        else:
            raise Exception(f"Not supported type({v}:{type(v)}).")
    return "&".join(
        [
            f"{quote(k, safe='-_.~')}={quote(str(v), safe='-_.~')}"
            for k, v in _qs.items()
        ]
    )


@single_cache
def signed_headers(headers: typing.Dict):
    return ";".join([n.lower().strip() for n in headers.keys()])


def sign_task_1(
    method,
    canonical_uri,
    header_set,
    request_query_set: dict,
    request_body="",
):
    """
    ************* TASK 1: CREATE A CANONICAL REQUEST *************
    http://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html

    :param method:
    :param canonical_uri:
    :param header_set:
    :param request_query_set:
    :param request_body:
    :return: canonical_request
    """
    # Step 1 is to define the verb (GET, POST, etc.)--already done.

    # Step 2: Create canonical URI--the part of the URI from domain to query
    # string (use '/' if no path)
    canonical_uri = quote(canonical_uri)

    # Step 3: Create the canonical query string. In this example (a GET request),
    # request parameters are in the query string. Query string values must
    # be URL-encoded (space=%20). The parameters must be sorted by name.
    # For this example, the query string is pre-formatted in the request_parameters variable.
    if method.upper() in [
        "POST",
    ]:
        cqs = ""
    else:
        cqs = canonical_querystring(request_query_set)

    # Step 4: Create the canonical headers and signed headers. Header names
    # must be trimmed and lowercase, and sorted in code point order from
    # low to high. Note that there is a trailing \n.
    canonical_headers = (
        "\n".join(f"{k}:{v}" for k, v in header_set.items()) + "\n"
    )

    # Step 5: Create the list of signed headers. This lists the headers
    # in the canonical_headers list, delimited with ";" and in alpha order.
    # Note: The request can include any headers; canonical_headers and
    # signed_headers lists those that you want to be included in the
    # hash of the request. "Host" and "x-amz-date" are always required.
    # signed_headers = 'host;x-amz-date'

    # Step 6: Create payload hash (hash of the request body content). For GET
    # requests, the payload is an empty string ("").
    if "x-amz-content-sha256" in header_set:
        payload_hash = request_body
    else:
        if isinstance(request_body, str):
            request_body = request_body.encode("utf-8")
        payload_hash = hashlib.sha256(request_body).hexdigest()

    # Step 7: Combine elements to create canonical request
    return (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{cqs}\n"
        f"{canonical_headers}\n"
        f"{signed_headers(header_set)}\n"
        f"{payload_hash}"
    )


def sign_task_2(
    service_name,
    region,
    amz_date,
    date_stamp,
    canonical_request,
):
    """
    ************* TASK 2: CREATE THE STRING TO SIGN*************

    :param service_name:
    :param region:
    :param amz_date:
    :param date_stamp:
    :param canonical_request:
    :return: string_to_sign
    """
    algorithm = const.get("__algorithm__")

    hashed_canonical_request = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()

    return (
        f"{algorithm}\n"
        f"{amz_date}\n"
        f"{credential_scope(date_stamp, region, service_name)}\n"
        f"{hashed_canonical_request}"
    )


def sign_task_3(secret_key, date_stamp, region, service, string_to_sign):
    """
    ************* TASK 3: CALCULATE THE SIGNATURE *************

    :param secret_key:
    :param date_stamp:
    :param region:
    :param service:
    :param string_to_sign:
    :return: signature
    """
    # Create the signing key using the function defined above.
    signing_key = get_signature_key(secret_key, date_stamp, region, service)

    # Sign the string_to_sign using the signing_key
    return hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def sign_task_4(algorithm, access_key, scope, signature, **kwargs):
    """
    ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************

    :param algorithm:
    :param access_key:
    :param scope:
    :param signature:
    :param kwargs: Additional header items
    :return: headers
    """
    # The signing information can be either in a query string value or in
    # a header named Authorization. This code shows how to use a header.
    # Create authorization header and add to request headers
    authorization_header = (
        f"{algorithm} Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers(kwargs)}, "
        f"Signature={signature}"
    )

    # The request can include any headers, but MUST include "host", "x-amz-date"
    # and (for this scenario) "Authorization". "host" and "x-amz-date" must
    # be included in the canonical_headers and signed_headers, as noted
    # earlier. Order here is not significant.
    # Python note: The 'host' header is added automatically by the Python
    # 'requests' library.
    headers = dict(**kwargs, Authorization=authorization_header)
    return headers
