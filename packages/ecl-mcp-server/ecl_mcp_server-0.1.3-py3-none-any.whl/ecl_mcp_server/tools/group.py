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
from ecl_mcp_server.utils import check_poolid, common_logger

common_logger.debug("Loading tools: %s", __name__)
group = core.Module().add_module("group")


# region log group


@group.tool()
async def create_log_group(request: models.LogGroupCreateVO) -> models.CreateLogGroupResponse:
    """新建日志组"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logGroup"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.CreateLogGroupResponse(**response.json())


@group.tool(description="")
async def update_log_group(request: models.LogGroupUpdateVO) -> models.UpdateLogGroupResponse:
    """编辑日志组"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logGroup/{request.id}"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.UpdateLogGroupResponse(**response.json())


@group.tool()
async def delete_log_group(request: models.DeleteLogGroupRequest) -> models.DeleteLogGroupResponse:
    """删除日志组"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logGroup/{request.id}"
    response = await builder.build_request("DELETE", url)
    response.raise_for_status()
    return models.DeleteLogGroupResponse(**response.json())


@group.tool()
async def query_log_group_list(request: models.QueryLogGroupListRequest) -> dict[str, Any]:
    """查询日志组列表"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logGroup/list"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


# endregion
