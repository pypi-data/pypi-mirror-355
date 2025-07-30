"""
类型守卫函数，帮助类型检查器理解数据类型
"""
from typing import TypeGuard, List, Optional, Any, Dict
from .models import QuakeService, QuakeHost, SimilarIconData, AggregationBucket


def is_service_list(data: Any) -> TypeGuard[List[QuakeService]]:
    """检查 data 是否是 QuakeService 列表"""
    return isinstance(data, list) and all(isinstance(item, QuakeService) for item in data)


def is_host_list(data: Any) -> TypeGuard[List[QuakeHost]]:
    """检查 data 是否是 QuakeHost 列表"""
    return isinstance(data, list) and all(isinstance(item, QuakeHost) for item in data)


def is_icon_list(data: Any) -> TypeGuard[List[SimilarIconData]]:
    """检查 data 是否是 SimilarIconData 列表"""
    return isinstance(data, list) and all(isinstance(item, SimilarIconData) for item in data)


def is_aggregation_dict(data: Any) -> TypeGuard[Dict[str, List[AggregationBucket]]]:
    """检查 data 是否是聚合结果字典"""
    if not isinstance(data, dict):
        return False
    for key, value in data.items():
        if not isinstance(key, str):
            return False
        if not isinstance(value, list):
            return False
        if not all(isinstance(item, AggregationBucket) for item in value):
            return False
    return True


def ensure_not_none(data: Optional[List[Any]]) -> List[Any]:
    """确保数据不是 None，如果是则返回空列表"""
    return data if data is not None else [] 