import json
import time
from datetime import datetime

import boto3


def main():
    sns_client = boto3.client(
        "sns",
    )

    # for _ in range(20):
    resp = sns_client.publish(
        TopicArn="arn:aws:sns:ap-northeast-2:{account_id}:TestNewTopic",
        Message="hello",
        MessageAttributes={
            "attr_1": {
                "DataType": "Number",
                "StringValue": "1000",
            }
        },
    )

    print(datetime.now())
    print(resp.get("MessageId"))
    time.sleep(30)


if __name__ == "__main__":
    main()
