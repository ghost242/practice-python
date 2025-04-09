import argparse
import logging
from collections import namedtuple
from datetime import datetime

import sqlalchemy
import sys

from pytz import timezone

RFC3339_FORMAT = "%Y-%m-%dT%H:%M:%S"
DEFAULT_MILI_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
MessageFormat = namedtuple("MessageFormat", ("type", "title", "body"))

parser: argparse.ArgumentParser = argparse.ArgumentParser(
    prog="job",
    conflict_handler="resolve",
    add_help=False,
    argument_default=argparse.SUPPRESS,
)

sub_parsers: dict = dict()


def str_to_datetime(
    str_datetime: str,
    dt_format: str = DEFAULT_MILI_FORMAT,
    tz: timezone = None,
) -> datetime:
    """
    convert str to datetime

    :param str str_datetime: target datetime text formatted `dt_format`
    :param str dt_format: date format. default '%Y-%m-%d %H:%M:%S.%f'
    :param timezone tz: timezone
    :return: datetime object
    :rtype: datetime
    """
    if str_datetime is None:
        pass

    converted_dt = datetime.strptime(str_datetime, dt_format)
    if tz:
        converted_dt = tz.localize(converted_dt)
    return converted_dt


def create_(
    sess,
    job_id_: str,
    *,
    name: str,
    owner: str,
):
    return MessageFormat("text", "created", "call create command")


def reserve_(
    sess,
    job_id_: str,
    *,
    status: str = "enable",
    begin_time: datetime,
    expired_time: datetime = None,
    period: str = None,
):
    return MessageFormat("text", "reserved", "call reserve command")


def update_(
    sess,
    job_id_: str,
    *,
    begin_time: datetime = None,
    expired_time: datetime = None,
    period: str = None,
    owner: str = None,
    name: str = None,
):
    return MessageFormat("text", "updated", "call update command")


def list_(
    sess,
):
    return MessageFormat("text", "listed", "call list command")


def add_create_parser(job_parser):
    create_parser = job_parser.add_parser(
        "create", help="새로운 Job을 만드는 명령어", add_help=False
    )

    create_parser.add_argument("--owner", help="Owner 이름/id.", required=True)
    create_parser.add_argument(
        "name",
        help="Job 이름. 사람이 읽을 수 있는 이름을 적는것을 권장하며, 만약 빈 값인 경우에 job_id 값을 넣는다.",
    )
    return create_parser


def add_reserve_parser(job_parser):
    reserve_parser = job_parser.add_parser(
        "reserve", help="이미 만들어진 Job을 스케줄에 등록하는 명령어", add_help=False
    )
    reserve_parser.add_argument(
        "--begin-time",
        help="Job 최초 실행 시간. (RFC3339; e,g, 2020-07-10T12:00:00)",
        required=True,
    )
    reserve_parser.add_argument(
        "--expire-time",
        help="Job 만료 시간. (RFC3339; e,g, 2020-07-10T12:00:00)",
    )
    reserve_parser.add_argument(
        "--period",
        help="Job 반복 주기.(sec 값 또는 cron 문법을 만족하는 값)",
    )
    reserve_parser.add_argument(
        "--status",
        default="enable",
        help="Job의 현재 상태. (기본값: enable)",
    )
    reserve_parser.add_argument(
        "job_id",
        help="스케줄에 등록할 Job의 id",
    )
    return reserve_parser


def add_update_parser(job_parser):
    update_parser = job_parser.add_parser(
        "update",
        help="이미 등록된 Job의 정보를 수정하는 명령어. Job에 대한 정보와 등록되어있는 스케줄 정보를 수정할 수 있다.",
        add_help=False,
    )

    update_parser.add_argument("-o", "--owner", help="Owner 이름/id.")
    update_parser.add_argument(
        "--name",
        help="Job 이름. 사람이 읽을 수 있는 이름을 적는것을 권장하며, 만약 빈 값인 경우에 job_id 값을 넣는다.",
    )
    update_parser.add_argument(
        "--begin-time",
        help="Job 실행 시간. (RFC3339; e,g, 2020-07-10T12:00:00)",
    )
    update_parser.add_argument(
        "--expire-time",
        help="Job 만료 시간. (RFC3339; e,g, 2020-07-10T12:00:00)",
    )
    update_parser.add_argument(
        "--period",
        help="Job 반복 주기.(sec 값 또는 cron 문법을 만족하는 값)",
    )
    update_parser.add_argument(
        "job_id",
        help="수정이 필요한 job id",
    )

    return update_parser


def add_help_parser(job_parser):
    help_parser = job_parser.add_parser(
        "help", help="명령어에 대한 사용법 및 도움말을 볼 수 있는 명령어", add_help=False
    )

    help_parser.add_argument(
        "-c",
        "--create",
        action="store_true",
        required=False,
        help="job create에 대한 명령어 사용법 및 도움말",
    )
    help_parser.add_argument(
        "-r",
        "--reserve",
        action="store_true",
        required=False,
        help="job reserve에 대한 명령어 사용법 및 도움말",
    )
    help_parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        required=False,
        help="job update에 대한 명령어 사용법 및 도움말",
    )
    help_parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        required=False,
        help="job list에 대한 명령어 사용법 및 도움말",
    )

    return help_parser


def init_parser():
    global parser
    global sub_parsers

    job_parser = parser.add_subparsers(
        title="commands", dest="command", metavar=""
    )

    sub_parsers = dict(
        create=add_create_parser(job_parser),
        reserve=add_reserve_parser(job_parser),
        update=add_update_parser(job_parser),
        list=job_parser.add_parser("list"),
        help=add_help_parser(job_parser),
    )

    return parser, sub_parsers


def job_handle(sess, params):
    res = parser.parse_args(params)

    parsed_res = vars(res)

    if parsed_res["command"] == "create":
        job_id = parsed_res.get("job_id")
        if "name" not in parsed_res or parsed_res["name"] is None:
            parsed_res["name"] = job_id

        res = create_(
            sess,
            job_id,
            classpath=parsed_res.get("classpath"),
            owner=parsed_res.get("owner"),
            product=parsed_res.get("product"),
            user=parsed_res.get("user"),
            name=parsed_res.get("name"),
        )
    elif parsed_res["command"] == "reserve":
        job_id = parsed_res.pop("job_id")
        begin_time = parsed_res.get("begin_time")
        expired_time = parsed_res.get("expire_time")

        if expired_time:
            expired_time = str_to_datetime(expired_time, RFC3339_FORMAT)

        res = reserve_(
            sess,
            job_id,
            status=parsed_res["status"],
            begin_time=str_to_datetime(begin_time, RFC3339_FORMAT),
            expired_time=expired_time,
            period=parsed_res.get("period"),
        )
    elif parsed_res["command"] == "update":
        job_id = parsed_res.pop("job_id")
        begin_time = parsed_res.get("begin_time", None)
        expired_time = parsed_res.get("expire_time", None)
        if begin_time:
            begin_time = str_to_datetime(begin_time, RFC3339_FORMAT)
        if expired_time:
            expired_time = str_to_datetime(expired_time, RFC3339_FORMAT)

        res = update_(
            sess,
            job_id,
            begin_time=begin_time,
            expired_time=expired_time,
            period=parsed_res.get("period", None),
            owner=parsed_res.get("owner", None),
            name=parsed_res.get("name", None),
        )
    elif parsed_res["command"] == "list":
        res = list_(sess)
    elif parsed_res["command"] == "help":
        title = "Get help text"
        if parsed_res["create"]:
            body = sub_parsers["create"].format_help()
        elif parsed_res["reserve"]:
            body = sub_parsers["reserve"].format_help()
        elif parsed_res["update"]:
            body = sub_parsers["update"].format_help()
        elif parsed_res["list"]:
            body = sub_parsers["list"].format_help()
        else:
            body = sub_parsers["help"].format_help()
        res = MessageFormat("text", title, body)
    else:
        raise Exception(f"Unknown command: {parsed_res['command']}")

    return res


def main():
    init_parser()

    print(["reserve", "--begin-time", "2020-01-02T10:11:12", "fake_job_id"])
    r = job_handle(
        None,
        ["reserve", "--begin-time", "2020-01-02T10:11:12", "fake_job_id"],
    )
    print(r)
    print(
        "create -c adsf --owner zxcv --name abcd ewi123"
    )
    r = job_handle(
        None,
        "create --owner zxcv --name abcd ewi123".split(
            " "
        ),
    )
    print(r)
    print(
        "update --begin-time 2020-09-23T01:02:03 --expire-time 2020-10-10T02:03:04 --period 100 ewi123"
    )
    r = job_handle(
        None,
        "update --begin-time 2020-09-23T01:02:03 --expire-time 2020-10-10T02:03:04 --period 100 ewi123".split(
            " "
        ),
    )
    print(r)
    print(
        "reserve --begin-time 2020-09-23T01:02:03 --expire-time 2020-10-10T02:03:04 --period 100 ewi123"
    )
    r = job_handle(
        None,
        "reserve --begin-time 2020-09-23T01:02:03 --expire-time 2020-10-10T02:03:04 --period 100 ewi123".split(
            " "
        ),
    )
    print(r)


if __name__ == "__main__":
    main()
