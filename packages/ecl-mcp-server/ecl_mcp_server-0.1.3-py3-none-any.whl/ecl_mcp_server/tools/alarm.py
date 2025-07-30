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

alarm = core.Module().add_module('alarm')


# region log alarm
@alarm.tool()
async def query_alarm_policy_detail(request: models.QueryAlarmPolicyDetailRequest) -> dict[str, Any]:
    """查询告警策略详情"""
    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/policy/detail/{request.policyId}'
    response = await builder.build_request('GET', url)
    response.raise_for_status()
    return response.json()


@alarm.tool()
async def query_alarm_policy_list(request: models.QueryAlarmPolicyListRequest) -> dict[str, Any]:
    """查询告警策略列表"""
    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/policy/list'
    response = await builder.build_request('GET', url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@alarm.tool()
async def query_alarm_record_list(request: models.QueryAlarmRecordListRequest) -> dict[str, Any]:
    """查询实时告警记录"""
    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/record/list'
    response = await builder.build_request('GET', url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@alarm.tool()
async def query_alarm_record_list_history(request: models.QueryAlarmRecordListRequest) -> dict[str, Any]:
    """查询历史告警记录"""
    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/record/list/history'
    response = await builder.build_request('GET', url, query_params=core.model_dump(request))
    response.raise_for_status()
    return response.json()


@alarm.tool()
async def confirm_alarm_record(request: models.ConfirmAlarmRecordRequest) -> models.ConfirmAlarmRecordResponse:
    """确认实时告警"""
    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/record/update/status'
    response = await builder.build_request('POST', url, data=core.model_dump(request))
    response.raise_for_status()
    return models.ConfirmAlarmRecordResponse(**response.json())


@alarm.tool()
async def delete_alarm_policy(request: models.DeleteAlarmPolicyRequest) -> models.DeleteAlarmPolicyResponse:
    """删除告警策略"""
    check_poolid(request)

    builder = OpenAPISignatureBuilder()
    url = f'{constants.HOST}/api/edw/edw/api/v1/journal/alarm/policy/delete/{request.policyId}'
    response = await builder.build_request('DELETE', url, query_params=core.model_dump(request))
    response.raise_for_status()
    return models.DeleteAlarmPolicyResponse(**response.json())

# endregion
