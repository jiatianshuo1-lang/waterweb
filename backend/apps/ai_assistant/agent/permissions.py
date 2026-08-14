"""
角色 → 工具权限矩阵

权限规则：
- super_admin / admin → 全部工具
- manager → 传感器查询 + 设备控制 + 知识库
- inspector / worker → 传感器查询 + 知识库 + 设备查看（不可控制）
- viewer → 仅传感器查询（只读）+ 知识库
"""

from typing import List

TOOL_PERMISSIONS = {
    "super_admin": "*",
    "admin": "*",
    "manager": [
        "query_water_level",
        "query_flow_rate",
        "query_soil_moisture",
        "query_weather",
        "query_water_quality",
        "query_station_status",
        "query_alerts",
        "query_irrigation_plan",
        "device_control",
        "device_status",
        "read_knowledge",
    ],
    "inspector": [
        "query_water_level",
        "query_flow_rate",
        "query_soil_moisture",
        "query_weather",
        "query_water_quality",
        "query_station_status",
        "query_alerts",
        "query_irrigation_plan",
        "device_status",
        "read_knowledge",
    ],
    "worker": [
        "query_water_level",
        "query_flow_rate",
        "query_soil_moisture",
        "query_weather",
        "query_water_quality",
        "query_station_status",
        "query_alerts",
        "device_status",
        "read_knowledge",
    ],
    "viewer": [
        "query_water_level",
        "query_flow_rate",
        "query_soil_moisture",
        "query_weather",
        "query_water_quality",
        "read_knowledge",
    ],
}


def can_use_tool(role: str, tool_name: str) -> bool:
    allowed = TOOL_PERMISSIONS.get(role, [])
    if allowed == "*":
        return True
    return tool_name in allowed


def filter_tools_by_role(role: str, all_tools: List[dict]) -> List[dict]:
    """根据角色过滤可用的工具定义列表"""
    return [t for t in all_tools if can_use_tool(role, t["name"])]
