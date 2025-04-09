from pprint import pprint

import boto3


def main():
    ecs = boto3.client(
        "ecs",
        region_name="ap-northeast-2",
    )

    tasks = ecs.list_tasks(
        cluster="test-cluster", desiredStatus="RUNNING"
    )
    tasks = tasks["taskArns"]

    res = ecs.describe_tasks(cluster="test-cluster", tasks=tasks)

    pprint(res)


if __name__ == "__main__":
    main()
