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
dashboard = core.Module().add_module("dashboard")


# region dashboard
@dashboard.tool()
async def query_dashboard_statistics(request: models.QueryDashboardStatisticsRequest) -> dict[str, Any]:
    """查询仪表盘列表"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/statistics"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@dashboard.tool()
async def create_dashboard(request: models.CreateDashboardRequest) -> models.CreateDashboardResponse:
    """新建仪表盘列表"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.CreateDashboardResponse(**response.json())


@dashboard.tool()
async def delete_dashboard(request: models.DeleteDashboardRequest) -> models.DeleteDashboardResponse:
    """删除仪表盘"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/{request.dashboardId}"
    response = await builder.build_request("DELETE", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return models.DeleteDashboardResponse(**response.json())


@dashboard.tool()
async def query_dashboard_chart(request: models.GetDashboardChartRequest) -> dict[str, Any]:
    """查询仪表盘下的图表列表"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/chats"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@dashboard.tool()
async def edit_dashboard(request: models.EditDashboardChartRequest) -> models.EditDashboardResponse:
    """编辑图表"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/chat/{request.chatId}"
    response = await builder.build_request("POST", url, data=core.model_dump(request))
    response.raise_for_status()
    return models.EditDashboardResponse(**response.json())


@dashboard.tool(description="")
async def delete_dashboard_chart(request: models.DeleteDashboardChartRequest) -> models.DeleteDashboardChartResponse:
    """删除图表"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/chat/{request.chatId}"
    response = await builder.build_request("DELETE", url)
    response.raise_for_status()
    return models.DeleteDashboardChartResponse(**response.json())


@dashboard.tool(description="")
async def query_chart_data(request: models.QueryDashboardChartDataRequest) -> dict[str, Any]:
    """查询图表数据"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/dashboard/chat/aggData"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


# endregion
