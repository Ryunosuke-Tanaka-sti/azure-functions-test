import azure.functions as func
import logging
import os
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

load_dotenv(".env.local")


@app.route(route="HTTPExample")
def HTTPExample(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    key = os.environ.get("KEY_VAULT_URL")
    credential = DefaultAzureCredential()  # 資格情報の取得

    client = SecretClient(vault_url=key, credential=credential)

    name = req.params.get("name")
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get("name")

    if name:
        return func.HttpResponse(
            f"Hello, {name}. This HTTP triggered function executed successfully."
        )
    else:
        test = client.get_secret("TEST")
        print(test.value)
        return func.HttpResponse(
            f"Hello, {test.value}. This HTTP triggered function executed successfully."
        )
