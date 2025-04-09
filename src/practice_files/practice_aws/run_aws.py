import os
from urllib.parse import urlparse

import boto3


def sqs_func():
    sqs = boto3.client("sqs")

    list_sqs = sqs.list_queues()

    # print(json.dumps(list_sqs, indent=4))

    queue_urls = [q for q in list_sqs["QueueUrls"]]

    # print(*queue_urls, sep='\n')

    for q in queue_urls:
        u = urlparse(q)
        name = u.path.split("/")[-1]

        if name[:4].lower() == "":
            print(q)
            sqs.delete_queue(QueueUrl=q)


def lambda_func():
    client = boto3.client("lambda")

    list_lambda = client.list_functions()
    list_layer = client.list_layers()

    # print(json.dumps(list_lambda, indent=4))
    # print(json.dumps(list_layer, indent=4))

    lambda_names = [n["FunctionName"] for n in list_lambda["Functions"]]
    layer_names = [
        (n["LayerName"], n["LatestMatchingVersion"]["Version"])
        for n in list_layer["Layers"]
    ]

    # print(*lambda_names, sep='\n')
    # print(*layer_names, sep='\n')
    #
    # for n, l in layer_names:
    #     if n[:4].lower() == '':
    #         print(n)
    #         client.delete_layer_version(
    #             LayerName=n,
    #             VersionNumber=l
    #         )

    for n in lambda_names:
        if n[:4].lower() == "":
            print(n)
            client.delete_function(FunctionName=n)


def cloudwatch_func():
    client = boto3.client("events")

    list_cloudwatch = client.list_rules()

    # print(json.dumps(list_cloudwatch, indent=4))

    rules = [r["Name"] for r in list_cloudwatch["Rules"]]

    # print(*rules, sep='\n')
    for r in rules:
        if r[:4].lower() == "":
            print(r)
            client.delete_rule(Name=r)


if __name__ == "__main__":
    # sqs_func()
    # lambda_func()
    cloudwatch_func()
