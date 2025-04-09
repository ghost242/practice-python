import requests
import json
from urllib.parse import urlparse

headers = {
    "Authorization": "token 40c6ce836b6aa38db8ab3ae47cbd6e44f248a595",
    "Accept": "application/vnd.github.v3+json",
}
params = {}
resp = requests.get(
    "https://api.github.com/repos/{account}/{repo}/releases/tags/{tagname}",
    params=params,
    headers=headers,
)

res = resp.json()

asset = list(filter(lambda a: "whl" in a["name"], res["assets"])).pop(-1)

filename, dl_url = asset["name"], asset["url"]
print(filename, dl_url)

dl_header = dict(**headers)
dl_header["Accept"] = "application/octet-stream"
dl_res = requests.get(dl_url, headers=dl_header)

with open(filename, "wb") as fd:
    for chunk in dl_res.iter_content(chunk_size=128):
        fd.write(chunk)
