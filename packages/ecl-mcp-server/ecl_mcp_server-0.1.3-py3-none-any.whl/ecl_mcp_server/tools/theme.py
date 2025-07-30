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
from ecl_mcp_server.openapi_signature import OpenAPISignatureBuilder
from ecl_mcp_server.utils import common_logger

common_logger.debug("Loading tools: %s", __name__)
theme = core.Module().add_module("theme")


# region log theme
@theme.tool()
async def create_index_set(request: models.CreateIndexSetRequest) -> models.CreateIndexSetResponse:
    """新建日志主题"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/indexSet"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.CreateIndexSetResponse(**response.json())


@theme.tool()
async def update_index_set(request: models.UpdateIndexSetRequest) -> models.UpdateIndexSetResponse:
    """编辑日志主题"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/indexSet/{request.id}"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.UpdateIndexSetResponse(**response.json())


@theme.tool()
async def delete_index_set(request: models.DeleteIndexSetRequest) -> models.DeleteIndexSetResponse:
    """删除日志主题"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/indexSet/{request.id}"
    response = await builder.build_request("DELETE", url)
    response.raise_for_status()
    return models.DeleteIndexSetResponse(**response.json())


@theme.tool()
async def query_log_theme_list(request: models.QueryIndexSetListRequest) -> dict[str, Any]:
    """查询日志主题列表"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/indexSet/list"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()

# endregion
