import requests


def main():
    res = requests.post(
        "http://localhost:8000/",
        data="hello world",
    )

    print(res, res.status_code, res.text, sep="\n")


if __name__ == "__main__":
    main()
