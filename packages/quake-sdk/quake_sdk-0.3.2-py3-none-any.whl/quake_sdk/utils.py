from typing import Union, List, Dict, Any
from .models import QuakeService, QuakeHost


def validate_quake_data(data: Union[QuakeService, QuakeHost, List[Union[QuakeService, QuakeHost]]]) -> Dict[str, Any]:
    """
    验证 Quake 数据的完整性和潜在问题
    
    Args:
        data: 单个或多个 QuakeService/QuakeHost 对象
        
    Returns:
        包含验证结果的字典，包括：
        - total_records: 总记录数
        - issues: 发现的问题列表
        - warnings: 警告信息列表
        - summary: 验证摘要
    """
    from datetime import datetime, timezone
    import warnings
    
    issues = []
    warnings_list = []
    records = []
    
    # 将输入标准化为列表
    if isinstance(data, (QuakeService, QuakeHost)):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        return {
            "total_records": 0,
            "issues": ["输入数据类型不支持"],
            "warnings": [],
            "summary": "验证失败"
        }
    
    future_time_count = 0
    missing_location_count = 0
    missing_service_count = 0
    
    for i, record in enumerate(records):
        record_issues = []
        
        # 检查时间字段
        if hasattr(record, 'time') and record.time:
            try:
                dt = datetime.fromisoformat(record.time.replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                if dt > current_time:
                    future_time_count += 1
                    record_issues.append(f"记录 {i}: 时间显示为未来时间 {record.time}")
            except:
                record_issues.append(f"记录 {i}: 时间格式无效 {record.time}")
        
        # 检查必要字段
        if isinstance(record, QuakeService):
            if not record.service:
                missing_service_count += 1
                record_issues.append(f"记录 {i}: 缺少服务信息")
            if not record.location:
                missing_location_count += 1
                record_issues.append(f"记录 {i}: 缺少地理位置信息")
        elif isinstance(record, QuakeHost):
            if not record.location:
                missing_location_count += 1
                record_issues.append(f"记录 {i}: 缺少地理位置信息")
        
        if record_issues:
            issues.extend(record_issues)
    
    # 生成警告
    if future_time_count > 0:
        warnings_list.append(f"发现 {future_time_count} 条记录的时间为未来时间，可能是测试数据或系统时间问题")
    
    if missing_location_count > 0:
        warnings_list.append(f"发现 {missing_location_count} 条记录缺少地理位置信息")
    
    if missing_service_count > 0:
        warnings_list.append(f"发现 {missing_service_count} 条记录缺少服务信息")
    
    # 生成摘要
    if not issues and not warnings_list:
        summary = "所有数据验证通过"
    elif issues:
        summary = f"发现 {len(issues)} 个数据问题"
    else:
        summary = f"数据基本正常，但有 {len(warnings_list)} 个警告"
    
    return {
        "total_records": len(records),
        "issues": issues,
        "warnings": warnings_list,
        "summary": summary,
        "details": {
            "future_time_records": future_time_count,
            "missing_location_records": missing_location_count,
            "missing_service_records": missing_service_count
        }
    } 