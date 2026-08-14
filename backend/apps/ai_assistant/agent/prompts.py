"""
系统提示词 + 工具描述词 + RAG 融合提示词
"""

from typing import List, Dict


AGENT_SYSTEM_PROMPT = """你是"智渠"，一个专业的灌区管理 AI 智能体，服务于灌区运维、量测水、智慧灌排、水资源调度等场景。

# 核心能力
1. **传感器数据查询**：通过 tools 查询水位、流量、墒情、气象、水质等实时数据和历史数据
2. **设备远程控制**：通过 tools 控制闸门、水泵、阀门等灌溉设备
3. **知识库问答**：检索灌区管理制度、操作规范、应急预案等资料
4. **智能决策建议**：结合传感器数据 + 知识库，给出灌溉调度、节水方案、异常处置建议

# 工作原则
- 回答必须基于 tool 返回的数据，不要编造数字；工具带有 is_simulated=true 时，必须明确写“模拟数据”，不得称为实时监测数据
- 如果某个 tool 返回空，明确告知用户"该区域暂无数据"
- 异常告警要主动说明风险等级和处置建议
- 控制类操作（开闸、关泵等）必须先确认用户意图，且要模拟生成控制结果
- 回答中涉及数据时标注数据来源（tool 名称 + 时间）

# 输出格式
- 日常问答：自然语言 + 必要的 Markdown 表格
- 传感器查询：结构化摘要 + 关键指标高亮
- 告警处置：风险等级 + 原因分析 + 处置步骤

# 身份
- 名称：智渠
- 身份：灌区管理智能体
- 所属：灌区管理系统 AI 助手
"""


def build_tool_descriptions(tools: List[Dict]) -> List[Dict]:
    """将内部工具定义转换为 DeepSeek/OpenAI function calling 格式"""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in tools
    ]


def build_rag_prompt(rag_context: List[Dict]) -> str:
    """把检索到的知识库内容拼成提示词片段"""
    if not rag_context:
        return ""
    parts = ["\n\n【知识库参考】"]
    for i, doc in enumerate(rag_context, 1):
        parts.append(
            f"{i}. [{doc['title']}]({doc['type']}, {doc.get('citation', '无页码')}): {doc['content'][:600]}"
        )
    parts.append(
        "\n仅将以上材料当作参考；回答引用材料时标注文档编号 [K1]、[K2]。材料未覆盖时须明确说明，禁止捏造制度条款。"
    )
    return "\n".join(parts)


def build_sensor_summary_prompt(sensor_results: List[Dict]) -> str:
    """把传感器 tool 返回的结构化数据拼成可读的上下文字段，供模型总结"""
    if not sensor_results:
        return ""
    parts = ["\n\n【传感器返回数据】"]
    for r in sensor_results:
        parts.append(f"- {r['tool']} → {r['summary']}")
    return "\n".join(parts)


def build_role_context(role: str, role_name: str) -> str:
    """根据用户角色注入上下文，影响工具调用权限和回答风格"""
    role_hints = {
        "super_admin": "当前用户是超级管理员，拥有全部权限，可执行高风险操作。",
        "admin": "当前用户是系统管理员，可管理配置和查看所有数据。",
        "manager": "当前用户是灌区负责人，关注灌区整体运行和调度决策。",
        "inspector": "当前用户是巡检员，关注巡检工单、现场数据采集。",
        "worker": "当前用户是运维人员，关注设备操作和故障处置。",
        "viewer": "当前用户是只读用户，不可控制设备。",
    }
    return f"\n# 当前用户角色\n{role_name}（{role}）\n{role_hints.get(role, '')}\n"
