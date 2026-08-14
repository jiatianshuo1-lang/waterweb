"""
Agent Tools 注册表 + 模拟传感器实现

所有传感器数据均为**离线模拟**（基于正态分布 + 历史基线 + 随机扰动），
不依赖真实硬件。每个 tool 返回统一结构：
{
    "success": True/False,
    "tool": "tool_name",
    "summary": "一句话摘要（供模型直接引用）",
    "data": {...},          # 结构化原始数据
    "generated_at": "ISO时间",
    "is_simulated": True,
}
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone


# ---------------------------------------------------------------------------
# 模拟基线：灌区各测站的"典型值"，用于生成贴近真实的传感器数据
# ---------------------------------------------------------------------------

STATION_BASELINES = {
    # 量测水站
    "WM-001": {"name": "总干渠首站", "type": "flow", "level_mean": 2.3, "level_std": 0.15,
               "flow_mean": 12.5, "flow_std": 2.0, "ph_mean": 7.2, "ph_std": 0.3},
    "WM-002": {"name": "东干渠中段", "type": "flow", "level_mean": 1.8, "level_std": 0.12,
               "flow_mean": 6.2, "flow_std": 1.2, "ph_mean": 7.4, "ph_std": 0.25},
    "WM-003": {"name": "西干渠尾端", "type": "flow", "level_mean": 1.2, "level_std": 0.10,
               "flow_mean": 3.1, "flow_std": 0.8, "ph_mean": 7.1, "ph_std": 0.3},
    "WM-004": {"name": "水库出水口", "type": "water_level", "level_mean": 35.6, "level_std": 0.5,
               "flow_mean": 8.0, "flow_std": 1.5, "ph_mean": 6.9, "ph_std": 0.2},
    # 墒情气象站
    "SM-001": {"name": "东灌区墒情站", "type": "comprehensive",
               "moisture_mean": 28.0, "moisture_std": 4.0, "ph_mean": 7.3, "ph_std": 0.4,
               "temp_mean": 26.0, "temp_std": 4.0, "humidity_mean": 65.0, "humidity_std": 10.0},
    "SM-002": {"name": "西灌区气象站", "type": "comprehensive",
               "moisture_mean": 22.0, "moisture_std": 5.0, "ph_mean": 7.5, "ph_std": 0.35,
               "temp_mean": 28.0, "temp_std": 5.0, "humidity_mean": 55.0, "humidity_std": 12.0},
    "SM-003": {"name": "北灌区墒情站", "type": "soil",
               "moisture_mean": 32.0, "moisture_std": 3.5, "ph_mean": 6.8, "ph_std": 0.3},
    "SM-004": {"name": "南灌区气象站", "type": "weather",
               "temp_mean": 30.0, "temp_std": 4.5, "humidity_mean": 70.0, "humidity_std": 11.0,
               "wind_mean": 2.5, "wind_std": 1.2},
}

STATION_LIST = [
    {"code": code, **info} for code, info in STATION_BASELINES.items()
]


def _gauss(mean: float, std: float, lo: Optional[float] = None, hi: Optional[float] = None) -> float:
    """高斯扰动 + 截断"""
    v = random.gauss(mean, std)
    if lo is not None:
        v = max(v, lo)
    if hi is not None:
        v = min(v, hi)
    return round(v, 2)


def _now_iso() -> str:
    return timezone.now().strftime("%Y-%m-%d %H:%M:%S")


def _result(tool: str, summary: str, data: Any, success: bool = True) -> Dict:
    return {
        "success": success,
        "tool": tool,
        "summary": summary,
        "data": data,
        "generated_at": _now_iso(),
        "is_simulated": True,
        "source": "waterweb-simulator",
        "data_quality": "simulated",
    }


# ---------------------------------------------------------------------------
# 工具 1：查询水位
# ---------------------------------------------------------------------------

def tool_query_water_level(station_code: Optional[str] = None, hours: int = 24) -> Dict:
    """查询水位数据（模拟）。station_code 可指定具体测站，留空则返回全部。"""
    target = None
    if station_code:
        target = STATION_BASELINES.get(station_code.upper())
        if not target:
            return _result("query_water_level", f"未找到测站 {station_code}", [], success=False)

    rows = []
    stations = [(station_code.upper(), target)] if target else [
        (c, i) for c, i in STATION_BASELINES.items() if "level_mean" in i
    ]

    for code, info in stations:
        mean = info["level_mean"]
        std = info.get("level_std", 0.1)
        current = _gauss(mean, std, lo=0.1)
        trend = "上升" if random.random() < 0.45 else ("下降" if random.random() < 0.9 else "平稳")
        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "current_level_m": current,
            "alert_level_m": round(mean * 1.25, 2),
            "status": "告警" if current > mean * 1.2 else "正常",
            "trend": trend,
            "measure_time": _now_iso(),
        })

    if len(rows) == 1:
        r = rows[0]
        summary = f"{r['station_name']} 当前水位 {r['current_level_m']}m，{r['status']}，趋势{r['trend']}"
    else:
        alert_cnt = sum(1 for r in rows if r["status"] == "告警")
        summary = f"共 {len(rows)} 个水位站，其中 {alert_cnt} 个告警"

    return _result("query_water_level", summary, rows)


# ---------------------------------------------------------------------------
# 工具 2：查询流量
# ---------------------------------------------------------------------------

def tool_query_flow_rate(station_code: Optional[str] = None, hours: int = 24) -> Dict:
    """查询流量数据（模拟）。"""
    target = None
    if station_code:
        target = STATION_BASELINES.get(station_code.upper())
        if not target:
            return _result("query_flow_rate", f"未找到测站 {station_code}", [], success=False)

    rows = []
    stations = [(station_code.upper(), target)] if target else [
        (c, i) for c, i in STATION_BASELINES.items() if "flow_mean" in i
    ]

    for code, info in stations:
        mean = info["flow_mean"]
        std = info.get("flow_std", 1.0)
        current = _gauss(mean, std, lo=0.1)
        total_24h = round(current * 3600 * 24 / 1000, 2)  # m³
        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "flow_rate_m3s": current,
            "total_flow_24h_m3": total_24h,
            "measure_time": _now_iso(),
        })

    if len(rows) == 1:
        r = rows[0]
        summary = f"{r['station_name']} 当前流量 {r['flow_rate_m3s']}m³/s，24h 累计 {r['total_flow_24h_m3']}m³"
    else:
        total = round(sum(r["flow_rate_m3s"] for r in rows), 2)
        summary = f"共 {len(rows)} 个流量站，当前总干渠流量 {total} m³/s"

    return _result("query_flow_rate", summary, rows)


# ---------------------------------------------------------------------------
# 工具 3：查询墒情
# ---------------------------------------------------------------------------

def tool_query_soil_moisture(station_code: Optional[str] = None, depth: str = "all") -> Dict:
    """查询土壤墒情（模拟）。depth 可选 0-10 / 10-20 / 20-40 / 40-60 / all"""
    target = None
    if station_code:
        target = STATION_BASELINES.get(station_code.upper())
        if not target:
            return _result("query_soil_moisture", f"未找到墒情站 {station_code}", [], success=False)

    rows = []
    stations = [(station_code.upper(), target)] if target else [
        (c, i) for c, i in STATION_BASELINES.items() if "moisture_mean" in i
    ]

    for code, info in stations:
        mean = info["moisture_mean"]
        std = info.get("moisture_std", 4.0)
        moisture = {
            "0-10cm": _gauss(mean - 2, std, lo=5, hi=50),
            "10-20cm": _gauss(mean, std, lo=5, hi=50),
            "20-40cm": _gauss(mean + 1, std * 0.8, lo=5, hi=55),
            "40-60cm": _gauss(mean + 2, std * 0.7, lo=5, hi=60),
        }
        if depth != "all" and depth in moisture:
            moisture = {depth: moisture[depth]}

        avg = round(sum(moisture.values()) / len(moisture), 2)
        ph = _gauss(info.get("ph_mean", 7.0), info.get("ph_std", 0.3), lo=5.5, hi=8.5)
        salinity = _gauss(1.2, 0.3, lo=0.3, hi=4.0)

        if avg < 18:
            status = "干旱预警"
        elif avg < 25:
            status = "偏干"
        elif avg < 35:
            status = "适宜"
        else:
            status = "偏湿"

        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "moisture_pct": moisture,
            "avg_moisture_pct": avg,
            "soil_ph": ph,
            "salinity_dsm": salinity,
            "status": status,
            "measure_time": _now_iso(),
        })

    if len(rows) == 1:
        r = rows[0]
        summary = f"{r['station_name']} 平均含水率 {r['avg_moisture_pct']}%，{r['status']}，pH={r['soil_ph']}"
    else:
        drought = sum(1 for r in rows if "干旱" in r["status"])
        summary = f"共 {len(rows)} 个墒情站，其中 {drought} 个存在干旱预警"

    return _result("query_soil_moisture", summary, rows)


# ---------------------------------------------------------------------------
# 工具 4：查询气象
# ---------------------------------------------------------------------------

def tool_query_weather(station_code: Optional[str] = None) -> Dict:
    """查询实时气象（模拟）。"""
    target = None
    if station_code:
        target = STATION_BASELINES.get(station_code.upper())
        if not target:
            return _result("query_weather", f"未找到气象站 {station_code}", [], success=False)

    rows = []
    stations = [(station_code.upper(), target)] if target else [
        (c, i) for c, i in STATION_BASELINES.items() if "temp_mean" in i
    ]

    wind_dirs = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]

    for code, info in stations:
        temp = _gauss(info["temp_mean"], info.get("temp_std", 4.0), lo=-5, hi=45)
        humidity = _gauss(info["humidity_mean"], info.get("humidity_std", 10.0), lo=15, hi=100)
        wind = _gauss(info.get("wind_mean", 2.0), info.get("wind_std", 1.0), lo=0, hi=15)
        solar = _gauss(500, 200, lo=0, hi=1200) if 6 <= datetime.now().hour <= 18 else random.uniform(0, 50)
        evap = round(random.uniform(1.5, 4.5), 2)
        rainfall = round(random.uniform(0, 25), 2) if random.random() < 0.3 else 0
        pressure = _gauss(1013, 15, lo=980, hi=1040)

        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "temperature_c": temp,
            "humidity_pct": humidity,
            "wind_speed_ms": wind,
            "wind_direction": random.choice(wind_dirs),
            "solar_radiation_wm2": round(solar, 1),
            "evapotranspiration_mm": evap,
            "rainfall_mm": rainfall,
            "pressure_hpa": pressure,
            "measure_time": _now_iso(),
        })

    if len(rows) == 1:
        r = rows[0]
        summary = (f"{r['station_name']} {r['temperature_c']}℃ / 湿度{r['humidity_pct']}% / "
                   f"风速{r['wind_speed_ms']}m/s{r['wind_direction']} / 今日降水{r['rainfall_mm']}mm")
    else:
        avg_temp = round(sum(r["temperature_c"] for r in rows) / len(rows), 1)
        total_rain = round(sum(r["rainfall_mm"] for r in rows), 1)
        summary = f"共 {len(rows)} 个气象站，平均气温 {avg_temp}℃，总降水 {total_rain}mm"

    return _result("query_weather", summary, rows)


# ---------------------------------------------------------------------------
# 工具 5：查询水质
# ---------------------------------------------------------------------------

def tool_query_water_quality(station_code: Optional[str] = None) -> Dict:
    """查询水质数据（模拟）。"""
    target = None
    if station_code:
        target = STATION_BASELINES.get(station_code.upper())
        if not target:
            return _result("query_water_quality", f"未找到测站 {station_code}", [], success=False)

    rows = []
    stations = [(station_code.upper(), target)] if target else [
        (c, i) for c, i in STATION_BASELINES.items() if "ph_mean" in i and "flow_mean" in i
    ]

    for code, info in stations:
        ph = _gauss(info.get("ph_mean", 7.2), info.get("ph_std", 0.3), lo=6.0, hi=9.0)
        turbidity = _gauss(15, 8, lo=0.5, hi=80)
        conductivity = _gauss(450, 150, lo=100, hi=1500)
        temp_water = _gauss(22, 4, lo=5, hi=35)
        quality_class = 1 if turbidity < 20 else (2 if turbidity < 50 else 3)

        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "ph": ph,
            "turbidity_ntu": round(turbidity, 1),
            "conductivity_uscm": round(conductivity, 1),
            "water_temp_c": round(temp_water, 1),
            "quality_class": quality_class,
            "quality_desc": ["优", "良", "一般", "较差"][min(quality_class, 3)],
            "measure_time": _now_iso(),
        })

    if len(rows) == 1:
        r = rows[0]
        summary = f"{r['station_name']} 水质{r['quality_desc']}（{r['quality_class']}类），pH={r['ph']}，浊度{r['turbidity_ntu']}NTU"
    else:
        summary = f"共 {len(rows)} 个水质站，整体水质良好"

    return _result("query_water_quality", summary, rows)


# ---------------------------------------------------------------------------
# 工具 6：查询测站状态
# ---------------------------------------------------------------------------

def tool_query_station_status(station_type: Optional[str] = None) -> Dict:
    """查询所有测站在线状态。station_type: flow / water_level / soil / weather / comprehensive"""
    rows = []
    type_filter = station_type

    for code, info in STATION_BASELINES.items():
        if type_filter and info.get("type") != type_filter:
            continue
        r = random.random()
        if r < 0.82:
            status, status_cn = "online", "在线"
        elif r < 0.92:
            status, status_cn = "offline", "离线"
        else:
            status, status_cn = "fault", "故障"

        rows.append({
            "station_code": code,
            "station_name": info["name"],
            "station_type": info.get("type", "unknown"),
            "status": status,
            "status_cn": status_cn,
            "last_data_time": _now_iso() if status == "online" else (
                timezone.now() - timedelta(minutes=random.randint(30, 720))
            ).strftime("%Y-%m-%d %H:%M:%S"),
        })

    online = sum(1 for r in rows if r["status"] == "online")
    offline = sum(1 for r in rows if r["status"] == "offline")
    fault = sum(1 for r in rows if r["status"] == "fault")
    summary = f"共 {len(rows)} 个测站，在线 {online}，离线 {offline}，故障 {fault}"

    return _result("query_station_status", summary, rows)


# ---------------------------------------------------------------------------
# 工具 7：查询告警
# ---------------------------------------------------------------------------

def tool_query_alerts(level: Optional[str] = None, limit: int = 10) -> Dict:
    """查询最近告警。level: info / warning / critical / emergency"""
    alert_pool = [
        {"type": "level_high", "title": "水位偏高告警", "message": "总干渠首站水位 2.85m，超警戒值 2.5m",
         "level": "warning", "station": "WM-001"},
        {"type": "flow_low", "title": "流量偏低告警", "message": "西干渠尾端流量仅 1.2m³/s，低于调度阈值 2.5",
         "level": "warning", "station": "WM-003"},
        {"type": "drought", "title": "干旱预警", "message": "北灌区墒情站 0-40cm 平均含水率 15.2%，低于适宜下限 18%",
         "level": "critical", "station": "SM-003"},
        {"type": "station_offline", "title": "测站离线告警", "message": "东干渠中段测站 2 小时未上报数据",
         "level": "info", "station": "WM-002"},
        {"type": "quality_abnormal", "title": "水质浊度异常", "message": "水库出水口浊度 45 NTU，超过日常值",
         "level": "warning", "station": "WM-004"},
        {"type": "rainfall", "title": "强降雨预警", "message": "南灌区气象站 1 小时降水 18mm，预计持续",
         "level": "critical", "station": "SM-004"},
    ]

    filtered = [a for a in alert_pool if not level or a["level"] == level]
    filtered = filtered[:limit]

    rows = []
    for a in filtered:
        rows.append({
            "alert_type": a["type"],
            "title": a["title"],
            "message": a["message"],
            "level": a["level"],
            "station_code": a["station"],
            "status": "未处理" if random.random() < 0.6 else "已处理",
            "triggered_at": _now_iso(),
        })

    critical_cnt = sum(1 for r in rows if r["level"] in ("critical", "emergency"))
    summary = f"共 {len(rows)} 条告警，其中 {critical_cnt} 条严重级别"

    return _result("query_alerts", summary, rows)


# ---------------------------------------------------------------------------
# 工具 8：查询灌溉计划
# ---------------------------------------------------------------------------

def tool_query_irrigation_plan(region: Optional[str] = None) -> Dict:
    """查询当前灌溉计划（模拟）。"""
    rows = [
        {"code": "IRR-2026-0814-001", "name": "东灌区晨灌计划", "region": "东干渠",
         "start_time": "今日 06:00", "end_time": "今日 09:30",
         "target_flow": 4.5, "total_water_m3": 5400, "status": "执行中"},
        {"code": "IRR-2026-0814-002", "name": "西灌区滴灌轮次", "region": "西干渠",
         "start_time": "今日 18:00", "end_time": "今日 22:00",
         "target_flow": 2.0, "total_water_m3": 2880, "status": "待执行"},
        {"code": "IRR-2026-0813-003", "name": "北灌区抗旱灌溉", "region": "北干渠",
         "start_time": "昨日 20:00", "end_time": "今日 02:00",
         "target_flow": 5.0, "total_water_m3": 10800, "status": "已完成"},
    ]
    if region:
        rows = [r for r in rows if region in r["region"] or region in r["name"]]

    running = sum(1 for r in rows if r["status"] == "执行中")
    summary = f"共 {len(rows)} 条灌溉计划，其中 {running} 条执行中"

    return _result("query_irrigation_plan", summary, rows)


# ---------------------------------------------------------------------------
# 工具 9：设备状态
# ---------------------------------------------------------------------------

def tool_device_status(device_code: Optional[str] = None) -> Dict:
    """查询灌溉设备状态（模拟）。"""
    devices = [
        {"code": "GV-001", "name": "总干渠首闸门", "type": "gate", "status": "online", "open_pct": 65},
        {"code": "GV-002", "name": "东干渠节制闸", "type": "gate", "status": "online", "open_pct": 40},
        {"code": "GV-003", "name": "西干渠尾闸", "type": "gate", "status": "online", "open_pct": 20},
        {"code": "PM-001", "name": "水库泵站1号", "type": "pump", "status": "running", "flow": 3.2, "power": 18.5},
        {"code": "PM-002", "name": "水库泵站2号", "type": "pump", "status": "stopped", "flow": 0, "power": 0},
        {"code": "VALVE-001", "name": "北灌区主控阀", "type": "valve", "status": "online", "open_pct": 80},
        {"code": "DRIP-001", "name": "滴灌片区A控制器", "type": "drip_control", "status": "online", "active_zones": 6},
    ]

    if device_code:
        devices = [d for d in devices if d["code"].upper() == device_code.upper()]
        if not devices:
            return _result("device_status", f"未找到设备 {device_code}", [], success=False)

    online = sum(1 for d in devices if d["status"] not in ("offline", "fault"))
    summary = f"共 {len(devices)} 台设备，{online} 台在线"

    return _result("device_status", summary, devices)


# ---------------------------------------------------------------------------
# 工具 10：设备控制（模拟）
# ---------------------------------------------------------------------------

def tool_device_control(device_code: str, action: str, value: Optional[float] = None) -> Dict:
    """
    控制灌溉设备（模拟，不会真的操作硬件）。
    action: open_gate / close_gate / set_gate / start_pump / stop_pump / set_valve
    value: 闸门开度 % 或流量 m³/s
    """
    device_pool = {
        "GV-001": {"name": "总干渠首闸门", "type": "gate"},
        "GV-002": {"name": "东干渠节制闸", "type": "gate"},
        "GV-003": {"name": "西干渠尾闸", "type": "gate"},
        "PM-001": {"name": "水库泵站1号", "type": "pump"},
        "PM-002": {"name": "水库泵站2号", "type": "pump"},
        "VALVE-001": {"name": "北灌区主控阀", "type": "valve"},
    }

    code = device_code.upper()
    dev = device_pool.get(code)
    if not dev:
        return _result("device_control", f"未找到设备 {device_code}", {}, success=False)

    # 动作映射
    action_map = {
        "open_gate": "闸门开启",
        "close_gate": "闸门关闭",
        "set_gate": f"闸门开度调整至 {value}%",
        "start_pump": "水泵启动",
        "stop_pump": "水泵停止",
        "set_valve": f"阀门开度调整至 {value}%",
    }

    if action not in action_map:
        return _result("device_control", f"不支持的操作: {action}", {}, success=False)
    if action in {"set_gate", "set_valve"} and (value is None or not 0 <= value <= 100):
        return _result("device_control", "开度必须提供且范围为 0-100%", {}, success=False)
    if action in {"open_gate", "close_gate", "start_pump", "stop_pump"} and value is not None:
        return _result("device_control", f"操作 {action} 不接受 value 参数", {}, success=False)

    # 模拟执行：95% 成功
    ok = random.random() < 0.95
    cmd_desc = action_map[action] if value is not None else action_map[action]

    if not ok:
        return _result("device_control", f"{dev['name']} {cmd_desc} → 执行超时（模拟）", {}, success=False)

    result_value = value
    if action == "open_gate":
        result_value = 100
    elif action == "close_gate":
        result_value = 0

    summary = f"{dev['name']}({code}) 执行「{cmd_desc}」→ 成功，当前值 {result_value}"
    return _result("device_control", summary, {
        "device_code": code,
        "device_name": dev["name"],
        "action": action,
        "target_value": value,
        "current_value": result_value,
        "executed_at": _now_iso(),
        "operator": "智渠 Agent (模拟)",
    })


# ---------------------------------------------------------------------------
# 工具 11：知识库检索（Agent 主动触发）
# ---------------------------------------------------------------------------

def tool_read_knowledge(query: str, top_k: int = 3) -> Dict:
    """从灌区知识库检索相关文件。"""
    from apps.ai_assistant.agent.rag import retrieve_knowledge
    docs = retrieve_knowledge(query, top_k=top_k)
    if not docs:
        return _result("read_knowledge", f"知识库中未找到与「{query}」相关的文档", [])
    summary = f"检索到 {len(docs)} 篇知识库文档，最相关：{docs[0]['title']}"
    return _result("read_knowledge", summary, docs)


# ---------------------------------------------------------------------------
# 工具注册表（按权限过滤 + DeepSeek function calling 格式）
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    "query_water_level": tool_query_water_level,
    "query_flow_rate": tool_query_flow_rate,
    "query_soil_moisture": tool_query_soil_moisture,
    "query_weather": tool_query_weather,
    "query_water_quality": tool_query_water_quality,
    "query_station_status": tool_query_station_status,
    "query_alerts": tool_query_alerts,
    "query_irrigation_plan": tool_query_irrigation_plan,
    "device_status": tool_device_status,
    "device_control": tool_device_control,
    "read_knowledge": tool_read_knowledge,
}


def get_tool_definitions() -> List[Dict]:
    """返回全部工具的 function calling schema"""
    return [
        {
            "name": "query_water_level",
            "description": "查询灌区各水位测站的实时水位、警戒水位、趋势变化",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_code": {"type": "string", "description": "测站编码，如 WM-001，可留空查询全部"},
                    "hours": {"type": "integer", "default": 24, "description": "查询最近多少小时"},
                },
            },
        },
        {
            "name": "query_flow_rate",
            "description": "查询各量测水站的瞬时流量、24小时累计流量",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_code": {"type": "string", "description": "测站编码，可留空"},
                    "hours": {"type": "integer", "default": 24},
                },
            },
        },
        {
            "name": "query_soil_moisture",
            "description": "查询墒情监测站不同深度的土壤含水率、pH、盐度",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_code": {"type": "string"},
                    "depth": {"type": "string", "enum": ["0-10cm", "10-20cm", "20-40cm", "40-60cm", "all"], "default": "all"},
                },
            },
        },
        {
            "name": "query_weather",
            "description": "查询气象站的气温、湿度、风速、降水、蒸发量等",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_code": {"type": "string"},
                },
            },
        },
        {
            "name": "query_water_quality",
            "description": "查询水质监测站的 pH、浊度、电导率、水质等级",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_code": {"type": "string"},
                },
            },
        },
        {
            "name": "query_station_status",
            "description": "查询所有测站的在线/离线/故障状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "station_type": {"type": "string", "enum": ["flow", "water_level", "soil", "weather", "comprehensive"]},
                },
            },
        },
        {
            "name": "query_alerts",
            "description": "查询灌区最近告警信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "string", "enum": ["info", "warning", "critical", "emergency"]},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        },
        {
            "name": "query_irrigation_plan",
            "description": "查询当前灌溉计划（执行中/待执行/已完成）",
            "parameters": {
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "区域关键词，如 东干渠"},
                },
            },
        },
        {
            "name": "device_status",
            "description": "查询灌溉设备（闸门/水泵/阀门）的运行状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_code": {"type": "string", "description": "设备编码，如 GV-001"},
                },
            },
        },
        {
            "name": "device_control",
            "description": "远程控制灌溉设备：开闸/关闸/调开度/启停水泵",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_code": {"type": "string", "description": "设备编码", "enum": ["GV-001", "GV-002", "GV-003", "PM-001", "PM-002", "VALVE-001"]},
                    "action": {"type": "string",
                               "enum": ["open_gate", "close_gate", "set_gate", "start_pump", "stop_pump", "set_valve"],
                               "description": "操作类型"},
                    "value": {"type": "number", "description": "目标开度%或流量m³/s"},
                },
                "required": ["device_code", "action"],
            },
        },
        {
            "name": "read_knowledge",
            "description": "从灌区知识库检索制度、规范、预案等文档",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词"},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["query"],
            },
        },
    ]


def invoke_tool(name: str, arguments: Dict) -> Dict:
    """安全调用工具（检查注册 + 参数转发）"""
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return {
            "success": False,
            "tool": name,
            "summary": f"未知工具: {name}",
            "data": None,
            "generated_at": _now_iso(),
            "is_simulated": True,
        }
    if not isinstance(arguments, dict):
        return _result(name, "工具参数必须为 JSON 对象", None, success=False)
    definition = next((item for item in get_tool_definitions() if item["name"] == name), {})
    properties = definition.get("parameters", {}).get("properties", {})
    unknown = set(arguments) - set(properties)
    if unknown:
        return _result(name, f"包含不支持的参数：{', '.join(sorted(unknown))}", None, success=False)
    try:
        return fn(**arguments)
    except Exception as e:
        return {
            "success": False,
            "tool": name,
            "summary": f"工具执行异常: {str(e)}",
            "data": None,
            "generated_at": _now_iso(),
            "is_simulated": True,
        }
