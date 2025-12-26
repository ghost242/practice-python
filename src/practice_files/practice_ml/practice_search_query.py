from litellm import text_completion
import json
import re
from typing import Literal

extractor = re.compile(r"```json(.*)```", re.DOTALL)


def convert_response_to_json(response: str) -> dict:
    regex = extractor.search(response)
    if regex:
        return json.loads(regex.group(1))
    elif response:
        return json.loads(response)
    else:
        raise Exception("No results")


def generate_search_query(
    industry_class: dict[Literal["keyword", "paraphrases"], list[str]],
    risk_factor: dict[Literal["keyword", "paraphrases"], list[str]],
) -> dict:
    prompt = """웹 검색엔진에 입력할 검색 쿼리를 생성해줘. 입력 값으로는 원본 키워드와 함께 유의어, 동의어가 주어진다. 생성되는 검색 쿼리는 필수 키워드로 지정된 요소를 반드시 포함해야 한다. 
    검색 쿼리는 최대 5개까지 생성하고, 모든 검색 쿼리는 한국어로 작성되어야 한다.
    ---
    필수 입력 키워드:
        * industry_class: {industry_class}
        * risk_factor: {risk_factor}
    ---
    출력 포멧
    ```json
    {{
        "search_queries": [
            "검색 쿼리 1",
            "검색 쿼리 2",
            "검색 쿼리 3"
        ]
    }}
    ```
    """

    form = """
        * 키워드: {keyword}
        * 유의어, 동의어: 
            {paraphrases}
    """

    response = text_completion(
        model="gpt-4o-mini",
        temperature=1.0,
        prompt=prompt.format(
            industry_class=form.format(
                keyword=industry_class["keyword"],
                paraphrases="\n".join(
                    [
                        f"- {paraphrase}"
                        for paraphrase in industry_class["paraphrases"]
                    ]
                ),
            ),
            risk_factor=form.format(
                keyword=risk_factor["keyword"],
                paraphrases="\n".join(
                    [
                        f"- {paraphrase}"
                        for paraphrase in risk_factor["paraphrases"]
                    ]
                ),
            ),
        ),
    )
    msg = response.choices[0].text
    query_result = convert_response_to_json(msg)

    return query_result


def refine_search_query(
    data: dict[Literal["search_queries"], list[str]],
) -> list[str]:
    prompt = """입력된 구문 목록은 검색엔진에 입력하기 위해 생성한 검색 쿼리 목록이다. 입력으로 주어진 쿼리 목록의 구문들을 다시 검토해서 단어들을 더 범용적인 단어로 치환하고 표현을 자연스럽게 다듬어줘.
    ---
    입력 쿼리 목록:
    
    {query_list}
    ---
    출력 포멧:
    ```json
    {{
        "search_queries": [
            "검색 쿼리 1",
            "검색 쿼리 2",
            "검색 쿼리 3"
        ]
    }}
    ```
    """

    response = text_completion(
        model="gpt-4o-mini",
        temperature=1.0,
        prompt=prompt.format(
            query_list="\n\n".join(
                ["* " + query for query in data["search_queries"]]
            )
        ),
    )

    msg = response.choices[0].text
    query_result = convert_response_to_json(msg)

    return query_result["search_queries"]


def find_paraphrases(
    keyword: str, *, description: str = "유의어, 동의어 검색이 필요한 키워드"
) -> dict[Literal["keyword", "paraphrases"], list[str]]:
    prompt = """입력으로 주어진 키워드와 관계된 유의어, 동의어를 추천해줘. 만약 유의어나 동의어가 없는 경우에는 키워드를 그대로 출력해줘.
    ---
    입력 키워드: `{keyword}`
    키워드 설명: `{description}`
    ---
    출력 포멧:
    ```json
    {{
        "keyword": "키워드",
        "paraphrases": ["유의어 1", "유의어 2", "유의어 3"]
    }}
    ```
    """

    response = text_completion(
        model="gpt-4o-mini",
        temperature=1.0,
        prompt=prompt.format(keyword=keyword, description=description),
    )

    msg = response.choices[0].text
    query_result = convert_response_to_json(msg)

    return query_result


if __name__ == "__main__":
    risk_factors = [
        "환율 변동 위험",
        "이자율 변동 위험",
        "지분가격 위험",
        "신용 위험",
        "유동성 위험",
        "자본 위험",
        "환율·이자율 등 금융시장 동향 변동",
        "세계 경기 침체·소비 둔화",
        "지정학적 긴장 지속",
        "사업 포트폴리오 (매각·인수) 결정 리스크",
        "주요 사업부 여건 급변",
        "제품 환경규제 (WEEE·RoHS·REACH·ErP)",
        "사업장 환경규제 (ISO 14001/45001 등)",
        "온실가스 배출권·탄소중립 법제",
        "컴플라이언스 (공정거래·영업비밀·제품책임 등)",
        "특허·디자인·라이선스 분쟁",
    ]
    for risk_factor in risk_factors[4:5]:
        class_paraphrases = find_paraphrases(
            "통신 및 방송장비 제조업 산업분야",
            description="한국표준산업분류에 제시되어있는 산업분야 이름",
        )
        risk_factor_paraphrases = find_paraphrases(
            risk_factor,
            description="기업 활동에서 발생할 수 있는 다양한 분야의 위험 요소 이름",
        )
        print(class_paraphrases)
        print(risk_factor_paraphrases)

        result = generate_search_query(
            class_paraphrases, risk_factor_paraphrases
        )
        print(result)
        # print(refine_search_query(result))
