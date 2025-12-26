import requests


def main():
    url = ""

    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type",
    }

    # Preflight request (OPTIONS)
    preflight = requests.options(url, headers=headers, timeout=60)
    print("Preflight (OPTIONS) status:", preflight.status_code)
    print("Preflight headers:", preflight.headers)
    print("Preflight body:", preflight.text)
    print("-" * 40)

    # Actual GET request with Origin header
    res = requests.get(
        url, headers={"Origin": "http://localhost:3000"}, timeout=60
    )
    print("GET status:", res.status_code)
    print("GET headers:", res.headers)
    print("GET body:", res.text)


if __name__ == "__main__":
    main()
