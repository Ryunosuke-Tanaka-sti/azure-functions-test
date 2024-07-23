import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def Create_aoai_client():
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    from openai import AzureOpenAI
    import os

    key = os.environ.get("KEY_VAULT_URL")
    credential = DefaultAzureCredential()  # 資格情報の取得
    client = SecretClient(vault_url=key, credential=credential)
    api_version = os.environ.get("AOAI_API_VERSION")
    api_key = client.get_secret("AOAI-API-KEY")
    entrypoint = client.get_secret("AOAI-ENDPOINT")
    aoai_client = AzureOpenAI(
        api_key=api_key.value,
        api_version=api_version,
        azure_endpoint=entrypoint.value,
    )
    return aoai_client


@app.function_name("AOAI_Chat")
@app.route(methods=[func.HttpMethod.POST])
def AOAI_Chat(req: func.HttpRequest) -> func.HttpResponse:
    import json

    logging.info("Python HTTP trigger function processed a request.")

    data = req.get_json()
    message = f"{data['message']}"

    aoai_client = Create_aoai_client()

    try:
        response = aoai_client.chat.completions.create(
            model="gpt-35-deploy",  # model = "deployment_name".
            messages=[
                {
                    "role": "system",
                    "content": """
                            以下の条件で文字列を採点してください。
                            - 文節ごとに区切って、文節ごとに得点をつけてください。
                            - ポジティブな単語ほど高い得点をつけてください。
                            - ネガティブな単語ほど低い得点をつけてください。
                            - 得点は100点から-100点までの範囲で評価してください。
                            - 得点が5の倍数にならないようにしてください。
                            - 同じ単語が複数回出てきた場合は、2つ目以降は得点を0にしてください。
                            - 文節ごとに得点を加算してください。
                            - 合計得点と文節ごとの得点を出力してください。
                            - 出力をJSON形式にしてフォーマットとしては以下に従ってください。また、このJSON以外は出力しないでください。
                            {
                                "totalScore": 116,
                                "words": [
                                    {"word": "美味しい", "score": 71},
                                    {"word": "ご飯を", "score": 32},
                                    {"word": "食べる", "score": 13},
                                ],
                            }
                    """,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )
        result = json.loads(response.choices[0].message.content)
        data = {
            "score": result["totalScore"],
            "message": message,
            "row": result,
        }

        return func.HttpResponse(
            json.dumps(data),
            mimetype="application/json",
        )

    except Exception as e:
        print(e)

    # name = req.params.get("name")
