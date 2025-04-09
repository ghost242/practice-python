"""
:mod: `AwsCloudwatchLogsHandler` -- log handler for cloudwatch logs
===================================================================

.. module:: AwsCloudwatchLogsHandler
    :platform: Unix, Windows
    :synopsis: logging to cloudwatch logs with logging functions.
.. moduleauther:: Ahram Oh <ohzakka@gmail.com>

"""

import logging
import time
import uuid
import warnings
from datetime import datetime
from logging import handlers

import boto3

# Default format
import typing

_AWS_CLOUDWATCHLOGS_FORMAT = logging.Formatter(
    "[%(name)s|%(levelname)s]%(asctime)s|%(module)s.%(funcName)s(%(lineno)s):%(message)s"
)

# fmt:off
RetentionDays = typing.Literal[-1, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
# fmt:on


class AwsCloudwatchLogsHandler(handlers.BaseRotatingHandler):
    """
    Set logging handler for write log on cloudwatch logs.

    :param str log_stream_name: Optional. Name of user want to run job.
    :param str log_group_name: It name for log group name.
    :param int log_retention_days: It is how long remains log message.
        It can be only in this values(1, 3, 5, 7, 14, 30, 60, 90, 120, 150,
        180, 365, 400, 545, 731, 1827, and 3653).
        If not in this values, this value will ignored.
    :param int buffer_flush_term: It is buffering term for avoid
        ThrottlingException.
    :param Optional[str] log_format: Log message format(ref.
        https://docs.python.org/3/library/logging.html#logrecord-attributes
        )
    """

    def close(self) -> typing.NoReturn:
        """
        Log handler close. It will flush remain log buffers.

        :return:
        :rtype: NoReturn
        """
        if self.__log_buffer:
            self.flush()

        super().close()

    def flush(self) -> typing.NoReturn:
        """
        Send log messages to log stream and make empty log buffer

        :return:
        :rtype: NoReturn
        """

        try:
            self.acquire()

            if self.__log_buffer:
                self.__sequence_token = self.client.put_log_events(
                    logGroupName=self.__log_group,
                    logStreamName=self.__log_stream_name,
                    logEvents=self.__log_buffer,
                    sequenceToken=self.__sequence_token,
                )
                self.__log_buffer.clear()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> typing.NoReturn:
        """
        log emitting function. log record will buffered in here.

        :param record: Log record created from functions 'debug', 'info', 'warning', 'error'
        :type record: logging.LogRecord
        :return:
        :rtype: NoReturn
        """
        try:
            self.acquire()

            msg = self.format(record)
            log_msg = [
                dict(
                    timestamp=int(round(record.created * 1000)),
                    message=msg,
                )
            ]

            if not self.__log_buffer:
                self.__log_buffer = [log_msg]
                self.__buffering_start = self.__buffering_end = time.time()
            else:
                self.__log_buffer.append(log_msg)
                self.__buffering_end = time.time()

            # For pretend too many flush log buffer
            if (
                self.__buffering_end - self.__buffering_start
                >= self.__buffer_flush_delay
            ):
                self.flush()
        finally:
            self.release()

    @property
    def log_group(self):
        return self.__log_group

    @property
    def log_stream_name(self):
        return self.__log_stream_name

    def _set_log_group(self, group_name):

        group_list = self.client.describe_log_groups(
            logGroupNamePrefix=group_name,
        )

        if len(group_list) == 0:
            self.client.create_log_group(
                logGroupName=group_name,
            )
            self.__log_group = group_name
        else:
            self.__log_group = group_list[0].logGroupName

    def _set_log_stream_name(self, stream_name):
        self.__log_stream_name = (
            f"{stream_name} [{datetime.now().date().isoformat()}]"
        )

        log_streams = self.client.describe_log_streams(
            logGroupName=self.__log_group,
            logStreamNamePrefix=self.__log_stream_name,
        )
        self.__sequence_token = ""
        if len(log_streams) == 0:
            self.client.create_log_stream(
                logGroupName=self.__log_group,
                logStreamName=self.__log_stream_name,
            )
        else:
            for log_stream in log_streams:
                if log_stream.logStreamName == self.__log_stream_name:
                    self.__sequence_token = log_stream.uploadSequenceToken
