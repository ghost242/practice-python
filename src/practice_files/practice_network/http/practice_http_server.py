"""
python3의 builtin 패키지를 이용한 http 서버. 과거에 캡스톤프로젝트에서 만들었던 코드의 기초적인 부분만 남겨서 샘플코드로 보관
"""

import json

from urllib.parse import parse_qs, unquote, urlparse

from http.server import BaseHTTPRequestHandler, HTTPServer


class CustomHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        req_url = urlparse(self.path)

        qs = parse_qs(req_url.query)

        if req_url.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                bytes(json.dumps(qs, sort_keys=True), encoding="utf8")
            )


def http_server():
    with HTTPServer(("localhost", 8080), CustomHTTPHandler) as httpd:
        httpd.serve_forever()


http_server()
