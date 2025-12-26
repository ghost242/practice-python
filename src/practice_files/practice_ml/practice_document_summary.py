from litellm import completion, batch_completion
from litellm.types.utils import ModelResponse
from pydantic import BaseModel, Field
import json
from datetime import datetime
import os
from typing import Generator

import re
from uuid import uuid4

from llama_index.llms.openai import OpenAI

import logging


logging.basicConfig(level=logging.INFO)

extractor = re.compile(r"```json\n(.*)\n```", re.DOTALL)


def reduce(data) -> dict:
    prompt = """입력할 값은 JSON 포멧으로 작성된 문서이고 "risk", "results" 두개 필드로 구성되어있다. 이 중에서 risk 필드의 값을 주제로 정의하고, results필드의 값이 처리해야 할 대상이다.
    results 필드의 값은 title, snippet, date, source, url 다섯개 필드로 구성된 object array이고, 제거할 object의 기준은 아래 목록으로 정의한다.
    
    * date 필드의 값이 최근 1년 이전인 경우
    * title, snippet 문맥이 주제와 관계가 없는 경우

    남은 results 필드의 값들은 변형이 없는 원본을 유지해야 하고, 주제와 관계가 있는 값들로 구성되어야 한다. 
    전체 출력은 JSON 포멧으로 작성해야 한다. 출력 결과는 반드시 `risk`, `results` 두개 필드로 구성되어야 한다.
    """

    num_results = len(data["results"])

    msg = ""
    total_results = {"risk": data["risk"], "results": []}

    try:
        response = completion(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {"content": prompt, "role": "system"},
                {"content": f"주제: {data['risk']}", "role": "user"},
                {
                    "content": f"원본 results: {json.dumps(data['results'])}",
                    "role": "user",
                },
            ],
        )
        msg = response.choices[0].message.content
        regex = extractor.search(msg)
        if regex:
            total_results["results"].extend(
                json.loads(regex.group(1))["results"]
            )
        elif msg:
            total_results["results"].extend(json.loads(msg)["results"])
        else:
            raise Exception("No results")

        return total_results
    except AttributeError as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e
    except Exception as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e


def subgroup(data) -> dict:
    prompt = """주제를 기반으로 요약 구문을 작성해줘. 원본 구문은 title, snippet, date, url, source 필드로 구성되어있다. 구문 요약을 위해 작업을 아래 단계로 나누어 진행한다.
    1. 모든 title, snippet 값을 분석한다.
    2. title, snippet 값의 공통 소재끼리 묶어서 섹션으로 구분한다.(공통 소재가 1개인 경우 section 하나만 생성한다.) 
    섹션으로 구분된 결과에서 모든 값은 원본을 유지해야 하고, 원본의 title, snippet, date, url, source 필드 값을 유지해야 한다. 출력 포멧은 JSON 포멧으로 작성해야 한다.
    출력 포멧
    ```json
    {
        "risk": "",  # 원본 risk 필드 값이 유지되어야 함
        "subjects": [
            {
                "subject": "",
                "sections": [
                    {
                        "title": "",
                        "snippet": "",
                        "date": "",
                        "url": "",
                        "source": ""
                    }
                ]
            }
        ]
    }
    ```
    """

    msg = ""

    try:
        response = completion(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"content": prompt, "role": "system"},
                {"content": json.dumps(data), "role": "user"},
            ],
        )
        msg = response.choices[0].message.content
        regex = extractor.search(msg)
        if regex:
            return json.loads(regex.group(1))
        elif msg:
            return json.loads(msg)
        else:
            raise Exception("No results")
    except AttributeError as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e
    except Exception as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e


class Summary(BaseModel):
    sections: list["Section"] = Field(description="섹션 목록")


class Section(BaseModel):
    title: str = Field(description="섹션 제목")
    content: str = Field(description="섹션 내용")
    citations: list["Citation"] = Field(description="참고 원본 목록")


class Citation(BaseModel):
    title: str = Field(description="참고 원본 제목")
    url: str = Field(description="참고 원본 URL")
    source: str = Field(description="참고 원본 출처")


def summarize(data) -> dict:
    # summary_prompt = """지금 입력할 값은 JSON 포맷으로 작성된 문서이고, risk, results 필드로 구성되어있다.
    # risk는 results 필드의 값을 검색 엔진으로부터 검색 결과로 얻기위한 검색어 소재이다.
    # results는 검색 엔진의 검색 결과 자체이고, risk 필드의 값과 관계가 높은 결과만 다시 정리한 목록이다.
    # 작업 목적은 results 필드의 각 object의 title, snippet을 통합해서 자연스러운 문장으로 요약 정리하는 것이다. 정리된 내용은 results 필드의 값들을 overview하는 내용이다.
    # 정리 결과물이 둘 이상의 소재로 구성되어있는 경우에는 독립된 섹션으로 구분되도록 나눠줘. 각 섹션에는 citations 필드를 통해서 원본의 title, url, source 필드 값으로 구성된 섹션의 원본을 식별할 수 있게 구성해줘.
    # 요약 구문은 한국어를 기본으로 작성되어야 한다. 이 결과는 JSON 포멧으로 출력되어야 한다.
    # """
    summary_prompt = """주제를 기반으로 요약 구문을 작성해줘. 원본 구문은 title, snippet, date, url, source 필드로 구성되어있다. 구문 요약을 위해 작업을 아래 단계로 나누어 진행한다.
    1. 모든 title, snippet 값을 분석한다.
    2. title, snippet 값의 공통 소재끼리 묶어서 섹션으로 구분한다.(공통 소재가 1개인 경우 section 하나만 생성한다.)
    3. 각 섹션에 대해서 자연스러운 문장으로 요약 정리한다.
    4. 각 섹션의 요약 정리 내용을 통합해서 주제와 관련된 내용을 포함한 최종 요약 구문을 작성한다.
    요약 구문은 한국어 기반의 자연스러운 문장으로 만들어져야 하고, 주제와 관련된 내용이 포함되어야 한다. 전체 요약 구문이 둘 이상의 소재로 구성되어있는 경우에는 독립된 섹션으로 구분되도록 나뉘어야 하고, 각 섹션에는 citations 필드를 통해서 원본의 title, url, source 필드 값으로 구성된 섹션의 원본을 식별할 수 있게 구성해줘.
    """
    # summary_prompt = """주제를 기반으로 요약 구문을 작성해줘. 원본 구문은 title, snippet, date, url, source 필드로 구성되어있다. 그 중에서 title, snippet 내용을 전부 읽고 분석해줘.
    # 그리고 분석 결과를 토대로 요약 구문을 자연스러운 문장으로 다시 생성해줘. 이 요약 구문은 주제와 관련된 내용을 포함해야 한다. 전체 요약 구문이 둘 이상의 소재로 구성되어있는 경우에는 독립된 섹션으로 구분되도록 나눠줘. 각 섹션에는 citations 필드를 통해서 원본의 title, url, source 필드 값으로 구성된 섹션의 원본을 식별할 수 있게 구성해줘.
    # 요약 구문은 한국어를 기본으로 작성되어야 한다. 이 결과는 JSON 포멧으로 출력되어야 한다.
    # ---
    # 원문:
    # {content}
    # """

    msg = ""

    try:
        response = completion(
            model="gpt-4o-mini",
            temperature=0.5,
            timeout=120,
            messages=[
                {"content": summary_prompt, "role": "system"},
                {"content": f"주제: {data['risk']}", "role": "user"},
                {"content": json.dumps(data), "role": "user"},
            ],
            response_format=Summary,
        )

        print(response)
        msg = response.choices[0].message.content
        regex = extractor.search(msg)
        if regex:
            return json.loads(regex.group(1))
        elif msg:
            return json.loads(msg)
        else:
            raise Exception("No results")
    except AttributeError as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e
    except Exception as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e


def batch_summary(data) -> Generator[dict, None, None]:
    summary_prompt = """주제를 기반으로 요약 구문을 작성해줘. 원본 구문은 title, snippet, date, url, source 필드로 구성되어있다. 구문 요약을 위해 작업을 아래 단계로 나누어 진행한다.
    1. 모든 title, snippet 값을 분석한다.
    2. title, snippet 값의 공통 소재끼리 묶어서 섹션으로 구분한다.(공통 소재가 1개인 경우 section 하나만 생성한다.)
    3. 각 섹션에 대해서 자연스러운 문장으로 요약 정리한다.
    4. 각 섹션의 요약 정리 내용을 통합해서 주제와 관련된 내용을 포함한 최종 요약 구문을 작성한다.
    요약 구문은 한국어 기반의 자연스러운 문장으로 만들어져야 하고, 주제와 관련된 내용이 포함되어야 한다. 전체 요약 구문이 둘 이상의 소재로 구성되어있는 경우에는 독립된 섹션으로 구분되도록 나뉘어야 하고, 각 섹션에는 citations 필드를 통해서 원본의 title, url, source 필드 값으로 구성된 섹션의 원본을 식별할 수 있게 구성해줘.
    """
    try:
        messages = [
            [
                {"content": summary_prompt, "role": "system"},
                {"content": f"주제: {item['risk']}", "role": "user"},
                {"content": json.dumps(item), "role": "user"},
            ]
            for item in data
        ]

        responses = batch_completion(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Summary,
        )

        for response in responses:
            msg = response.choices[0].message.content
            regex = extractor.search(msg)
            if regex:
                yield json.loads(regex.group(1))
            elif msg:
                yield json.loads(msg)
            else:
                raise Exception("No results")
    except Exception as e:
        logging.debug(f"message: {msg}\nerror: {e}")
        raise e


def runner():
    with open("sample-4.json", "r") as f:
        data = json.load(f)
    now = datetime.now().strftime("%y%m%d%H%M")
    dir_path = f"test_results/summary-{now}"
    os.makedirs(dir_path, exist_ok=True)

    pipe = {}

    files = []

    # for item in data[3:5]:
    # # for _ in range(1):
    #     # item = data[7]
    #     # pipe["reduced"] = reduce(item)
    #     # pipe["subgrouped"] = subgroup(item)
    #     pipe["summarized"] = summarize(item)
    #     files.append(f"{dir_path}/{item['risk']}-{uuid4()}.json")
    #     with open(files[-1], "w") as f:
    #         json.dump(pipe, f, indent=2, ensure_ascii=False)

    for idx, item in enumerate(batch_summary(data)):
        files.append(
            f"{dir_path}/{data[idx]['risk'].replace(' ', '')}-{uuid4()}.json"
        )
        with open(files[-1], "w") as f:
            json.dump(item, f, indent=2, ensure_ascii=False)

    print(*files, sep="\n")


if __name__ == "__main__":
    runner()
