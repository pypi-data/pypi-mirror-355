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

from typing import Any

from ecl_mcp_server import constants, core, models
from ecl_mcp_server.context import context
from ecl_mcp_server.openapi_signature import OpenAPISignatureBuilder
from ecl_mcp_server.utils import check_poolid, common_logger

common_logger.debug("Loading tools: %s", __name__)

etl = core.Module().add_module("etl")


@etl.tool()
async def list_log_fn(request: models.ListLogFnRequest) -> dict[str, Any]:
    """查询数据加工规则列表"""
    if not request.poolIds and context.preferredPoolId:
        request.poolIds = [context.preferredPoolId]

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logFn/list"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@etl.tool()
async def query_log_fn(request: models.QueryLogFnDetailRequest) -> dict[str, Any]:
    """查询数据加工规则详情"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logFn/{request.azId}"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@etl.tool()
async def delete_log_fn(request: models.DeleteLogFnDetailRequest) -> dict[str, Any]:
    """删除数据加工规则"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logFn/delete/{request.azId}"
    response = await builder.build_request("DELETE", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@etl.tool()
async def update_log_fn_status(request: models.UpdateLogFnStatusRequest) -> dict[str, Any]:
    """修改数据加工规则启停状态"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logFn/status"
    response = await builder.build_request("PUT", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()
