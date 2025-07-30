#  Copyright © 2025 China Mobile (SuZhou) Software Technology Co.,Ltd
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import copy
import hmac
import os
import time
import urllib
import urllib.parse
import uuid
from hashlib import sha1, sha256
from typing import Any, Literal

import httpx
from pydantic import BaseModel, SecretStr

from ecl_mcp_server import constants
from ecl_mcp_server.utils import secret_from_env


def percent_encode(encode_str):
    encode_str = str(encode_str)
    res = urllib.parse.quote(encode_str.encode("utf-8"), "")
    res = res.replace("+", "%20")
    res = res.replace("*", "%2A")
    res = res.replace("%7E", "~")

    return res


def _sort_params(query_params):
    parameters = copy.deepcopy(query_params)

    if "Signature" in parameters:
        parameters.pop("Signature")

    sorted_parameters = sorted(parameters.items(), key=lambda kv: kv[0])
    return sorted_parameters


def _keep_query_params_nonnull(query_params):
    if query_params is None:
        return {}
    new_query_params = {}
    for k, v in query_params.items():
        if v is not None:
            new_query_params[k] = v
    return new_query_params


class OpenAPISignatureBuilder:
    def __init__(self, access_key: str | None = None, secret_key: str | SecretStr | None = None, **kwargs):
        if access_key is None:
            access_key = secret_from_env(constants.ENV_JOURNAL_AK_KEY)().get_secret_value()
        if secret_key is None:
            secret_key = secret_from_env(constants.ENV_JOURNAL_SK_KEY)()

        self.access_key = access_key
        self.secret_key = secret_key if isinstance(secret_key, SecretStr) else SecretStr(secret_key)
        self.signature_version = "V2.0"
        self.signature_method = "HmacSHA1"
        self.user_agent = kwargs.get("user_agent") or "journal-mcp-server/1.0"

    def sign(
        self,
        http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        query_params: dict[str, Any],
        servlet_path: str,
    ):
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())

        query_params["Timestamp"] = time_str
        query_params["AccessKey"] = self.access_key
        query_params["SignatureMethod"] = self.signature_method
        query_params["SignatureNonce"] = uuid.uuid4().hex
        query_params["SignatureVersion"] = self.signature_version

        sorted_parameters = _sort_params(query_params)

        canonicalized_query_string = ""

        for k, v in sorted_parameters:
            canonicalized_query_string += "&" + percent_encode(k) + "=" + percent_encode(v)

        string_to_sign = http_method + "\n" + percent_encode(servlet_path) + "\n" + sha256(canonicalized_query_string[1:].encode("utf-8")).hexdigest()

        key = ("BC_SIGNATURE&" + self.secret_key.get_secret_value()).encode("utf-8")
        string_to_sign = string_to_sign.encode("utf-8")
        signature = hmac.new(key, string_to_sign, sha1).hexdigest()

        return signature

    async def build_request(self, http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"], url: str, /, *, query_params: dict[str, Any] = None, json: BaseModel = None, **kwargs) -> httpx.Response:
        """Builds and sends a signed HTTP request

        Features:
            1. Automatically generates API signature and adds to query_params
            2. Handles Pydantic model data conversion
            3. Sets default User-Agent header
            4. Supports passing through all native httpx parameters

        Args:
            http_method: HTTP request method (GET/POST/PUT/PATCH/DELETE)
            url: Complete request URL
            query_params: URL query parameters dictionary
            json: Request body data as Pydantic model
            **kwargs: Other parameters supported by httpx.request

        Returns:
            httpx.Response: Request response object
        """
        query_params = _keep_query_params_nonnull(query_params)

        parsed_url = urllib.parse.urlparse(url)
        signature = self.sign(http_method, query_params, parsed_url.path)
        query_params["Signature"] = signature

        _kwargs = copy.deepcopy(kwargs)
        if "headers" not in _kwargs:
            _kwargs["headers"] = {}
        headers = _kwargs.get("headers")
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.user_agent

        if json is not None:
            _kwargs["json"] = json.model_dump(mode="json")
            headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            return await client.request(http_method, url, params=query_params, **_kwargs)


async def _test():  # pragma: no cover
    import constants

    # Request URL
    url = "https://ecloud.10086.cn/api/edw/edw/api/v1/journal/web/overview/alarmProductTopN"
    headers = {"Content-Type": "application/json"}
    # Common signature parameters, add other parameters here if needed
    query_params = {
        "startTime": "2025-01-01 00:00:00",
        "endTime": "2025-01-01 10:00:00",
    }
    access_key = os.getenv(constants.ENV_JOURNAL_AK_KEY)
    secret_key = os.getenv(constants.ENV_JOURNAL_SK_KEY)

    builder = OpenAPISignatureBuilder(access_key, secret_key)
    response = await builder.build_request("GET", url, query_params=query_params, headers=headers)

    import curlify  # [optional] uv add curlify or uv pip install curlify

    # Convert to curl command
    ci = curlify.to_curl(response.request)
    # Print the curl command and response
    print(ci)
    print(response.json())


if __name__ == "__main__":
    import asyncio

    asyncio.run(_test())
