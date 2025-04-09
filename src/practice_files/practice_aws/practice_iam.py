import boto3


def main():
    client = boto3.client("sts")
    userid = 0

    res = client.assume_role(
        RoleArn=f"arn:aws:iam::{userid}:role/ecsInstanceRole",
        RoleSessionName="ecsInstanceSession",
    )

    print(res)


if __name__ == "__main__":
    main()
