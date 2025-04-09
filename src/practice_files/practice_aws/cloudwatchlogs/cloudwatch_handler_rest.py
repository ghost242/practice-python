import logging

# Default format
import time
import warnings

from ..signing import config_credentials
from ..rest.cloudwatch_logs import (
    LogMessage,
    create_log_group,
    create_log_stream,
    describe_log_groups,
    describe_log_streams,
    put_log_events,
    put_retention_policy,
)


aws_cloudwatchlogs_format = logging.Formatter(
    "[%(name)s|%(levelname)s]%(asctime)s|%(module)s.%(funcName)s(%(lineno)s):%(message)s"
)


class AwsCloudwatchLogsHandler(logging.Handler):
    def __init__(
        self,
        *,
        aws_access_key=None,
        aws_secret_key=None,
        aws_session_token=None,
        region=None,
        job_name="N/A",
        container_name="N/A",
        log_retention_days=None,
        buffer_flush_term=1,
    ) -> None:
        """
        Set logging handler for write log on cloudwatch logs.

        :param buffer_flush_term:
        :param aws_access_key: Optional. AWS access key about user access token.
            May environment is EC2, This value is not need.
        :param aws_secret_key: Optional. AWS secret key about user access token.
            May environment is EC2, This value is not need.
        :param region: Optional. User using AWS service code name where region
            (e.g., ap-northeast-2)
        :param job_name: Optional. Name of user want to run job.
        :param container_name: It name for log group name.
        :param log_retention_days: It is how long remains log message.
            It can be only in this values(1, 3, 5, 7, 14, 30, 60, 90, 120, 150,
            180, 365, 400, 545, 731, 1827, and 3653).
            If not in this values, this value will ignored.
        :param buffer_flush_term: It is buffering term for avoid ThrottlingException.
        """
        logging.Handler.__init__(self)

        config_credentials(
            access_key=aws_access_key,
            secret_key=aws_secret_key,
            session_token=aws_session_token,
            region=region,
        )

        self.log_group = container_name
        self.log_stream_name = job_name
        self.__log_buffer = list()

        if log_retention_days:
            if log_retention_days in [
                1,
                3,
                5,
                7,
                14,
                30,
                60,
                90,
                120,
                150,
                180,
                365,
                400,
                545,
                731,
                1827,
                3653,
            ]:
                put_retention_policy(
                    self.__log_group,
                    log_retention_days,
                )
            else:
                warnings.warn(
                    f"This retention days is not valid. {log_retention_days=}",
                    UserWarning,
                )

        self.setFormatter(aws_cloudwatchlogs_format)
        self.__buffer_flush_delay = buffer_flush_term
        self.__buffering_start, self.__buffering_end = 0, 0

    def close(self) -> None:
        if self.__log_buffer:
            self.flush()

        super().close()

    def flush(self) -> None:
        try:
            self.acquire()

            if self.__log_buffer:
                self.__sequence_token = put_log_events(
                    self.__log_group,
                    self.__log_stream_name,
                    self.__log_buffer,
                    self.__sequence_token,
                )
                self.__log_buffer.clear()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.acquire()

            msg = self.format(record)

            if not self.__log_buffer:
                self.__log_buffer = [
                    LogMessage(
                        timestamp=int(round(record.created * 1000)),
                        message=msg,
                    )
                ]
                self.__buffering_start = self.__buffering_end = time.time()
            else:
                self.__log_buffer.append(
                    LogMessage(
                        timestamp=int(round(record.created * 1000)),
                        message=msg,
                    )
                )
                self.__buffering_end = time.time()

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

    @log_group.setter
    def log_group(self, container_name):
        self.__log_group = f"/{container_name}"

        group_list = describe_log_groups(self.__log_group)

        if len(group_list) == 0:
            create_log_group(
                self.__log_group,
            )
        else:
            log_group_info = group_list[0]
            self.__log_group = log_group_info.logGroupName

    @log_stream_name.setter
    def log_stream_name(self, job_name):
        self.__log_stream_name = (
            f"{job_name} [{date_util.now().date().isoformat()}]"
        )

        log_streams = describe_log_streams(
            self.__log_group,
            self.__log_stream_name,
        )
        self.__sequence_token = ""
        if len(log_streams) == 0:
            create_log_stream(
                self.__log_group,
                self.__log_stream_name,
            )
        else:
            for log_stream in log_streams:
                if log_stream.logStreamName == self.__log_stream_name:
                    self.__sequence_token = log_stream.uploadSequenceToken
