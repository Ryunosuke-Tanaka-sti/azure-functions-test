import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def Create_aoai_client():
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    from openai import AzureOpenAI
    import os

    api_version = os.environ.get("AOAI_API_VERSION")
    api_key = os.environ.get("AOAI_API_KEY")
    entrypoint = os.environ.get("AOAI_ENDOPOINT")
    aoai_client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=entrypoint,
    )
    return aoai_client


# def Create_cosmos_container():
#     from azure.cosmos import CosmosClient
#     import os
#     from azure.keyvault.secrets import SecretClient
#     from azure.identity import DefaultAzureCredential
#     import os

#     key = os.environ.get("KEY_VAULT_URL")
#     credential = DefaultAzureCredential()  # 資格情報の取得
#     client = SecretClient(vault_url=key, credential=credential)
#     try:
#         api_key = os.environ.get("COSMOS_API_KEY")
#         uri = os.environ.get("COSMOS_URI")

#         api_key = client.get_secret("COSMOS-API-KEY")
#         uri = client.get_secret("COSMOS-URL")

#         client = CosmosClient(url=uri.value, credential=api_key.value)

#         database_name = os.environ.get("COSMOS_DATABASE_NAME")
#         container_name = os.environ.get("COSMOS_CONTAINER_NAME")

#         db = client.get_database_client(database_name)
#         container = db.get_container_client(container_name)
#         return 1, container
#     except Exception as err:
#         return 0, err


@app.function_name("AOAI_Chat")
@app.route(methods=[func.HttpMethod.POST])

# https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-add-output-binding-cosmos-db-vs-code?tabs=isolated-process%2Cv2&pivots=programming-language-python
# https://qiita.com/neet_and_neet/items/5e82aec8a25752ce16aa
def AOAI_Chat(
    req: func.HttpRequest,
) -> func.HttpResponse:
    import json

    logging.info("Python HTTP trigger function processed a request.")

    data = req.get_json()
    message = f"{data['message']}"

    aoai_client = Create_aoai_client()

    try:
        response = aoai_client.chat.completions.create(
            model="gpt-4o",  # model = "deployment_name".
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
                    "content": "いつも色々と配慮して頂き本当に感謝です",
                },
                {
                    "role": "assistant",
                    "content": """{
                            "totalScore": 127,
                            "words": [
                                {"word": "いつも", "score": 3},
                                {"word": "色々と", "score": -7},
                                {"word": "配慮して", "score": 14},
                                {"word": "頂き", "score": 38},
                                {"word": "本当に", "score": 6},
                                {"word": "感謝です", "score": 73},
                            ],
                        }""",
                },
                {
                    "role": "user",
                    "content": "今週は忙しすぎてしんどい",
                },
                {
                    "role": "assistant",
                    "content": """{
                        "totalScore": -84,
                        "words": [
                            {"word": "今週は", "score": 19},
                            {"word": "忙しすぎて", "score": -21},
                            {"word": "しんどい", "score": -82},
                        ],
                    }""",
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
        )
        try:
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
            check = aoai_client.chat.completions.create(
                model="gpt-4o",  # model = "deployment_name".
                messages=[
                    {
                        "role": "system",
                        "content": "以下の情報がJson形式で読み込むことができません。修正してJsonで出力してください。",
                    },
                    {
                        "role": "user",
                        "content": response.choices[0].message.content,
                    },
                ],
            )
            result = json.loads(check.choices[0].message.content)

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
        logging.error(e)
        data = {
            "score": 0,
            "message": "エラーが出ちゃいました",
            "row": e,
        }
        return func.HttpResponse(
            json.dumps(data),
            mimetype="application/json",
        )
    # name = req.params.get("name")
