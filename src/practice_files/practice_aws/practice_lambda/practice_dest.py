import boto3
import json
import os


def main():
    sns = boto3.client("sns")

    topics = sns.list_topics()

    print("--Topics--", topics, sep="\n")

    arn = list(
        filter(lambda t: "TestTriggerTopic" in t["TopicArn"], topics["Topics"])
    ).pop()

    print("--Arn--", arn, sep="\n")

    subs = sns.list_subscriptions_by_topic(
        TopicArn=arn["TopicArn"],
    )

    sub = list(
        filter(
            lambda s: "TestLambdaFunc" in s["Endpoint"], subs["Subscriptions"]
        )
    ).pop()

    print("--Subscription--", sub, sep="\n")

    resp = sns.publish(
        TopicArn=arn["TopicArn"], Message=json.dumps({"Success": False})
    )

    print("--Publish Result--", resp)


if __name__ == "__main__":
    main()
