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

from datetime import datetime
from typing import (
    Generic,
    List,
    Literal,
    Optional,
    TypeVar,
)

from pydantic import (
    BaseModel,
    Field,
    create_model,
    field_serializer,
    model_validator,
)
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from ecl_mcp_server.attr import PoolIdAttr
from ecl_mcp_server.utils import deserialize_datetime, deserialize_datetime_optional, serialize_datetime

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    code: str = Field(..., description="错误码，包括：000000：成功，其他：失败")
    message: str = Field(..., description="响应结果信息提示")
    state: str = Field(..., description="接口调试状态，可选值：ERROR（调试错误）、OK（接口调试成功）")
    entity: Optional[T] = Field(None, description="响应实体")


class PageRequestModel(BaseModel, Generic[T]):
    pageNum: Optional[int] = Field(1, description="当前页码")
    pageSize: Optional[int] = Field(50, description="每页显示记录数")
    commonParam: T = Field(..., description="请求参数内容")


class DateTimeRangeModel(BaseModel):
    startTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="开始时间")
    endTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="结束时间")

    @model_validator(mode="after")
    def validate_time_range(cls, data):
        if data.startTime > data.endTime:
            raise ValueError("startTime must ≤ endTime")
        return data

    @field_serializer("startTime")
    def serialize_starttime(self, data: datetime) -> str:
        return serialize_datetime(data)

    @field_serializer("endTime")
    def serialize_endtime(self, data: datetime) -> str:
        return serialize_datetime(data)


class GetLogDataParam(BaseModel, PoolIdAttr):
    indexSetId: str = Field(..., description="日志主题 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")
    fromTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="查询日志的起始时间")
    toTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="查询日志的结束时间")
    queryString: Optional[str] = Field(None, description="查询内容。使用 Lucene 查询语法表达")

    @field_serializer("fromTime")
    def serialize_starttime(self, data: datetime) -> str:
        return serialize_datetime(data)

    @field_serializer("toTime")
    def serialize_endtime(self, data: datetime) -> str:
        return serialize_datetime(data)

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class GetLogDataRequest(PageRequestModel[GetLogDataParam], PoolIdAttr):
    def get_pool_id(self) -> Optional[str]:
        return self.commonParam.get_pool_id()

    def set_pool_id(self, pool_id: Optional[str]):
        self.commonParam.set_pool_id(pool_id)


class AlarmProductTopNRequest(DateTimeRangeModel):
    pass


class AlarmLogGroupTopNRequest(DateTimeRangeModel):
    pass


class DeleteLogGroupRequest(BaseModel):
    id: str = Field(..., description="日志组 ID")


class QueryLogGroupListRequest(BaseModel):
    keyword: Optional[str] = Field(None, description="关键字")
    poolIds: Optional[List[str]] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")
    pageNum: Optional[int] = Field(None, description="当前页码")
    pageSize: Optional[int] = Field(None, description="每页显示记录数")


class CreateIndexSetRequest(BaseModel, PoolIdAttr):
    logGroupId: str = Field(..., description="日志组 ID")
    indexPrefix: str = Field(..., description="日志主题名称")
    description: Optional[str] = Field(None, description="描述")
    storeDays: int = Field(..., ge=1, le=180, description="存储天数，取值为 1~180 天")
    poolId: Optional[str] = Field(..., description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class UpdateIndexSetRequest(BaseModel):
    id: str = Field(..., description="日志主题 ID")
    description: Optional[str] = Field(None, description="描述")
    storeDays: int = Field(..., ge=1, le=180, description="存储天数，取值为 1~180 天")


class DeleteIndexSetRequest(BaseModel):
    id: str = Field(..., description="日志主题 ID")


class QueryIndexSetListRequest(QueryLogGroupListRequest):
    logGroupId: Optional[str] = Field(None, description="日志组 ID")


class QueryAlarmPolicyDetailRequest(BaseModel):
    policyId: str = Field(..., description="告警策略 ID")


class QueryAlarmPolicyListRequest(QueryIndexSetListRequest):
    indexSetId: Optional[str] = Field(None, description="日志主题 ID")


class QueryAlarmRecordListRequest(BaseModel):
    poolIds: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")
    productType: Optional[str] = Field(None, description="日志源类型")
    policyId: Optional[str] = Field(None, description="策略 ID")
    logIndexId: Optional[str] = Field(None, description="日志主题 ID")
    logGroupId: Optional[str] = Field(None, description="日志组 ID")
    startTime: Annotated[Optional[datetime], BeforeValidator(deserialize_datetime_optional)] = Field(None, description="开始时间")
    endTime: Annotated[Optional[datetime], BeforeValidator(deserialize_datetime_optional)] = Field(None, description="结束时间")
    orderByColumn: Optional[str] = Field(None, description="排序字段：createTime 或者 updateTime 或者 alarmTimes")
    orderByRule: Optional[str] = Field(None, description="排序规则：DESC 或者 ASC；其中 DESC 为降序，ASC 为升序")
    pageNum: Optional[str] = Field(None, description="页码")
    pageSize: Optional[str] = Field(None, description="页面大小")

    @field_serializer("startTime")
    def serialize_starttime(self, data: datetime) -> Optional[str]:
        if data is None:
            return None
        return serialize_datetime(data)

    @field_serializer("endTime")
    def serialize_endtime(self, data: datetime) -> Optional[str]:
        if data is None:
            return None
        return serialize_datetime(data)


class ConfirmAlarmRecordRequest(BaseModel):
    ids: List[str] = Field(..., description="告警记录 ID")


class DeleteAlarmPolicyRequest(BaseModel, PoolIdAttr):
    policyId: str = Field(..., description="策略 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class QueryDashboardStatisticsRequest(BaseModel, PoolIdAttr):
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class CreateDashboardRequest(BaseModel, PoolIdAttr):
    name: str = Field(..., description="仪表盘名称")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class DeleteDashboardRequest(BaseModel, PoolIdAttr):
    dashboardId: str = Field(..., description="仪表盘 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class GetDashboardChartRequest(BaseModel, PoolIdAttr):
    dashboardId: str = Field(..., description="仪表盘 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class EditDashboardChartRequest(BaseModel):
    chatId: str = Field(..., description="图表 ID")
    name: str = Field(..., description="图表名称")


class DeleteDashboardChartRequest(BaseModel):
    chatId: str = Field(..., description="图表 ID")


class QueryDashboardChartDataRequest(DateTimeRangeModel):
    chatId: str = Field(..., description="图表 ID")


class LogAlarmProductTopNVO(BaseModel):
    productType: str = Field(..., description="产品类型")
    alarmNum: int = Field(..., description="告警个数", ge=0)  # int32 类型，ge=0 表示非负整数


class ListLogFnRequest(BaseModel):
    poolIds: Optional[List[str]] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")
    projectId: Optional[str] = Field(None, description="日志组 ID")
    sourceName: Optional[str] = Field(None, description="源日志主题名称")
    storeName: Optional[str] = Field(None, description="目标日志主题名称")
    orderByTime: Optional[Literal["DESC", "ASC"]] = Field(None, description="排序方式，降序取值：DESC，升序取值：ASC")
    pageNum: Optional[int] = Field(None, description="页码")
    pageSize: Optional[int] = Field(None, description="页面大小")


class QueryLogFnDetailRequest(BaseModel, PoolIdAttr):
    azId: int = Field(..., description="加工规则 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class DeleteLogFnDetailRequest(QueryLogFnDetailRequest):
    pass


class UpdateLogFnStatusRequest(BaseModel, PoolIdAttr):
    azId: int = Field(..., description="加工规则 ID")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")
    status: Literal["RUNNING", "STOP"] = Field(..., description="启停状态。启动取值为：RUNNING；停止取值为：STOP")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class AlarmTrendVO(BaseModel):
    date: str = Field(..., description="日期")
    count: int = Field(..., description="告警数量，包含实时告警和历史告警的持续次数")


class LogAlarmGroupTopNVO(BaseModel):
    indexPrefix: str = Field(..., description="日志主题")
    alarmNum: str = Field(..., description="告警个数")


class LogGroupCreateVO(BaseModel, PoolIdAttr):
    logGroupName: str = Field(..., description="日志组名称。5~32 位字符，支持英文、数字、中划线、下划线，需英文开头，不区分大小写")
    description: Optional[str] = Field(None, description="描述")
    poolId: Optional[str] = Field(None, description="资源池 ID，取值请参考云日志帮助中心")

    def get_pool_id(self) -> Optional[str]:
        return self.poolId

    def set_pool_id(self, pool_id: Optional[str]):
        self.poolId = pool_id


class LogGroupUpdateVO(BaseModel):
    id: str = Field(None, description="日志组 ID")
    logGroupName: str = Field(..., description="日志组名称。5~32 位字符，支持英文、数字、中划线、下划线，需英文开头，不区分大小写")
    description: Optional[str] = Field(None, description="日志组描述")


class LogGroupVO(BaseModel):
    """日志组详情实体"""

    id: str = Field(..., description="日志组 ID")
    logGroupName: str = Field(..., description="日志组名称")
    userId: str = Field(..., description="用户 ID")
    createTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="创建时间（date-time 格式）")
    description: str = Field(..., description="描述")
    indexSetNum: int = Field(..., description="日志主题数量")
    poolId: str = Field(..., description="资源池 ID")
    poolName: str = Field(..., description="资源池名称")


class DwPage(BaseModel, Generic[T]):
    """分页响应实体（包裹 LogGroupVO 列表）"""

    total: int = Field(..., description="总记录数")
    pageSize: int = Field(..., description="每页显示记录数")
    pageNum: int = Field(..., description="当前页")
    pageCount: int = Field(..., description="总页数")
    content: Optional[List[T]] = Field(None, description="内容")


class IndexSetVO(BaseModel):
    id: str = Field(..., description="日志主题 ID")
    userId: str = Field(..., description="用户 ID")
    logGroupId: str = Field(..., description="日志组 ID")
    logGroupName: str = Field(..., description="日志组名称")
    indexPrefix: str = Field(..., description="日志主题名称")
    description: str = Field(..., description="描述")
    storeDays: int = Field(..., description="存储天数")
    createTime: Annotated[datetime, BeforeValidator(deserialize_datetime)] = Field(..., description="创建时间（date-time 格式）")
    poolId: str = Field(..., description="资源池 ID")
    poolName: str = Field(..., description="资源池名称")


LogAlarmProductTopNResponse = ResponseModel[List[LogAlarmProductTopNVO]]
LogAlarmTrendResponse = ResponseModel[List[AlarmTrendVO]]
LogAlarmGroupTopNResponse = ResponseModel[List[LogAlarmGroupTopNVO]]
CreateLogGroupResponse = create_model("CreateLogGroupResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="日志组 ID")))
UpdateLogGroupResponse = create_model("UpdateLogGroupResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
DeleteLogGroupResponse = create_model("DeleteLogGroupResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))

QueryLogGroupListResponse = ResponseModel[DwPage[LogGroupVO]]
CreateIndexSetResponse = create_model("CreateIndexSetResponse", __base__=ResponseModel[str], entity=(Optional[int], Field(description="日志主题 ID")))
UpdateIndexSetResponse = create_model("UpdateIndexSetResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
DeleteIndexSetResponse = create_model("DeleteIndexSetResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
QueryIndexSetListResponse = ResponseModel[DwPage[IndexSetVO]]
ConfirmAlarmRecordResponse = create_model("ConfirmAlarmRecordResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
DeleteAlarmPolicyResponse = create_model("DeleteAlarmPolicyResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
CreateDashboardResponse = create_model("CreateDashboardResponse", __base__=ResponseModel[str], entity=(Optional[str], Field(description="仪表盘 ID")))

DeleteDashboardResponse = create_model("DeleteDashboardResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))

EditDashboardResponse = create_model("EditDashboardResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))
DeleteDashboardChartResponse = create_model("DeleteDashboardChartResponse", __base__=ResponseModel[int], entity=(Optional[int], Field(description="此次操作数据的条数，通常为 1")))

if __name__ == "__main__":
    pass
