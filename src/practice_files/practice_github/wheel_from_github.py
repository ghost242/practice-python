import sys
import os
import importlib.util

if importlib.util.find_spec("requests") is None:
    p = os.popen("pip install --user requests", mode="w")

    p.close()

requests = importlib.import_module("requests")


def download_wheel(token, pack_name, version_no):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    rel_url = "https://api.github.com/repos/{account}/{package}/releases/tags/{version}"
    resp = requests.get(
        rel_url.format(package=pack_name, version=version_no),
        headers=headers,
    )

    if resp.status_code >= 400:
        raise Exception(
            "Error get release({}) info in repo tag({}). Reason: {}".format(
                pack_name, version_no, resp.content
            )
        )

    res = resp.json()

    # get latest asset for wheel file
    asset = (
        list(filter(lambda a: "whl" in a["name"], res["assets"]))
        .sort(key=lambda a: a["name"], reverse=True)
        .pop()
    )

    if asset is None:
        raise Exception("Not found asset of wheel file")

    filename, dl_url = asset["name"], asset["url"]

    dl_header = dict(**headers)
    dl_header["Accept"] = "application/octet-stream"
    dl_res = requests.get(dl_url, headers=dl_header)

    if resp.status_code >= 400:
        raise Exception("Error get wheel file ")

    with open(filename, "wb") as fd:
        for chunk in dl_res.iter_content(chunk_size=128):
            fd.write(chunk)


def run_unpacking_wheel(pack_name):
    pip._internal.main(["install", "--target", pack_name, "python"])


def main(token, pack_name, version_info):
    download_wheel(token, pack_name, version_info)


if __name__ == "__main__":
    if not len(sys.argv) > 1:
        raise Exception(
            "Too few argument\n"
            "Usage: python3 wheel_from_github.py <package name> <tag name>\n"
        )
    main(os.environ["token"], sys.argv[1], sys.argv[2])
