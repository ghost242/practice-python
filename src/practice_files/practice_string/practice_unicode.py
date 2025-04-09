import json


def write_file():
    with open("text_unicode.txt") as rd:
        content = rd.read()

        print(content[22])

        with open("text_output.txt", "w") as wd:
            wd.write(content)


def read_text():
    value = [
        {
            "rejectedTitle": "[광고 문구] 미작성",
            "rejectedContent": "등록하신 광고 문구가 기재되지 않아 광고 등록이 보류되었습니다. - 수정방법 : 광고 문구는 이미지 소재 및 랜딩URL과 관련된 내용으로 올바르게 작성해 주시기 바랍니다.",
        }
    ]
    text = json.dumps(value, ensure_ascii=False)

    print(text[22])
    with open("text_output.txt", "w") as wd:
        wd.write(text)


def main():
    read_text()


if __name__ == "__main__":
    main()
