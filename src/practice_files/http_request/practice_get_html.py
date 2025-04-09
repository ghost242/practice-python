import requests


def main():
    res = requests.get("https://www.google.com")

    print(res.content)


if __name__ == "__main__":
    main()
