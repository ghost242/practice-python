import io
from urllib.parse import urlparse

from ctypes import string_at
from sys import getsizeof

import boto3


def get_s3(ACCESS_KEY, SECRET_KEY, bucket, key):
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    res = s3_client.list_objects_v2(
        Bucket=bucket,
        # Key=key
    )

    return res


def get_athena(ACCESS_KEY, SECRET_KEY):
    athena_client = boto3.client(
        "athena",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    res = athena_client.list_data_catalogs()

    for k, v in res.items():
        print(k, *v, sep="\n")

    res = athena_client.list_databases(CatalogName="AwsDataCatalog")

    for k, v in res.items():
        print(k, *v, sep="\n")

    res = athena_client.list_table_metadata(
        CatalogName="AwsDataCatalog",
        DatabaseName="database",
    )

    print(res)

    return res


def get_object(ACCESS_KEY, SECRET_KEY, bucket, key):
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    obj = s3.Object(bucket, key)

    string_stream = io.BytesIO()

    obj.download_fileobj(string_stream)

    print(string_stream.getvalue())
    # memview = string_stream.getbuffer()

    return string_stream.getvalue()


def put_object(ACCESS_KEY, SECRET_KEY, bucket, key, byte_obj):
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    obj = s3.Object(bucket, key)
    obj.upload_fileobj(byte_obj)


def main():
    path = "s3://bucket/prefix/object"
    s3_path = urlparse(path)
    # print(s3_path)
    # for i, d in enumerate(s3_path):
    #     print(i, d)
    bucket = s3_path.netloc
    full_path = s3_path.path.split("/")
    path = "/".join(full_path[:-1])
    key_name = full_path[-1]

    # print(bucket, path, key_name)
    res = get_object(
        "",
        "",
        bucket,
        s3_path.path[1:],
    )
    print(res)
    print(res.decode())
    write_data = io.BytesIO(res)
    put_object(
        "",
        "",
        bucket,
        "resource/write_test.txt",
        write_data,
    )


if __name__ == "__main__":
    main()
