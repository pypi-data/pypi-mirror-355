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

import datetime
from typing import Any

from ecl_mcp_server import constants, core, models
from ecl_mcp_server.context import context
from ecl_mcp_server.openapi_signature import OpenAPISignatureBuilder
from ecl_mcp_server.utils import check_poolid, common_logger, serialize_datetime

common_logger.debug("Loading tools: %s", __name__)

default = core.Module().add_module("default")


# region extra


@default.tool()
async def get_current_datetime() -> str:
    """获取当前日期时间"""
    return serialize_datetime(datetime.datetime.now(tz=context.tz))


# endregion

# region get log


@default.tool()
async def get_log(request: models.GetLogDataRequest) -> dict[str, Any]:
    """查询日志原文"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/logSearch/message"
    response = await builder.build_request("POST", url, json=request)
    response.raise_for_status()
    return response.json()


# endregion


# region log outline


@default.tool(description="")
async def query_alarm_product_topn(request: models.AlarmProductTopNRequest) -> models.LogAlarmProductTopNResponse:
    """查询告警资源类型 TOP5"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/overview/alarmProductTopN"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return models.LogAlarmProductTopNResponse(**response.json())


@default.tool()
async def query_alarm_trend() -> models.LogAlarmTrendResponse:
    """查询近 7 天告警趋势"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/overview/alarmTrend"
    response = await builder.build_request("GET", url)
    response.raise_for_status()
    return models.LogAlarmTrendResponse(**response.json())


@default.tool()
async def query_alarm_log_group_topn(request: models.AlarmLogGroupTopNRequest) -> models.LogAlarmGroupTopNResponse:
    """查询告警日志主题 Top5"""
    builder = OpenAPISignatureBuilder()
    url = f"{constants.HOST}/api/edw/edw/api/v1/journal/web/overview/alarmLogGroupTopN"
    response = await builder.build_request("GET", url, query_params=core.model_dump(request))
    response.raise_for_status()
    return models.LogAlarmGroupTopNResponse(**response.json())

# endregion
