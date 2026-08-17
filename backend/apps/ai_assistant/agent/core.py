"""
Agent 核心：LLM → function calling → 工具调度 → 多轮循环 → 最终回答

支持的 LLM：DeepSeek (推荐)、OpenAI 兼容端点、Azure OpenAI、本地 Ollama
所有提供方统一走 DeepSeek-Chat-Completions 协议（/v1/chat/completions + tools）。
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from . import tools as tool_module
from . import prompts as prompt_module
from . import permissions as perm_module
from .rag import retrieve_knowledge
from .context import build_context

logger = logging.getLogger("apps.ai_assistant")


# ---------------------------------------------------------------------------
# LLM 调用：统一接口，自动根据 provider 选 URL
# ---------------------------------------------------------------------------

PROVIDER_URLS = {
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "azure": None,  # Azure URL 由 config.api_url 指定（完整）
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "doubao": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "ollama": None,  # Ollama 走本地
}


_CHAT_PATH_HINTS = ("/chat/completions", "/completions")


def _resolve_api_url(configured: str, default: str) -> str:
    """
    用户可能填：
      - 完整路径：https://api.deepseek.com/v1/chat/completions  → 原样用
      - 只给 base：https://api.deepseek.com / https://api.deepseek.com/ → 拼上 default 的 path
      - Azure/Ollama 这种 default=None 的 → 原样用（用户必须填完整）
    """
    if not configured:
        return default
    lower = configured.lower().rstrip("/")
    if any(hint in lower for hint in _CHAT_PATH_HINTS):
        return configured.rstrip("/")
    if default:
        from urllib.parse import urlparse
        parsed = urlparse(default)
        return f"{configured.rstrip('/')}{parsed.path}"
    return configured


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def call_llm(
    messages: List[Dict],
    tools: List[Dict],
    config,
    stream: bool = False,
) -> Dict[str, Any]:
    """
    调用 LLM，支持 function calling。
    返回 LLM 原始 choice 对象（包含 content 或 tool_calls）。
    """
    provider = config.provider or "deepseek"
    configured_url = (config.api_url or "").strip()
    default_url = PROVIDER_URLS.get(provider, PROVIDER_URLS["deepseek"])

    if provider == "ollama":
        default_url = "http://localhost:11434/v1/chat/completions"

    if configured_url:
        api_url = _resolve_api_url(configured_url, default_url)
    else:
        api_url = default_url

    if not api_url:
        raise ValueError(f"未配置 {provider} 的 API 地址")

    payload: Dict[str, Any] = {
        "model": config.model_name,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": stream,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    try:
        resp = requests.post(
            api_url,
            json=payload,
            headers=_build_headers(config.api_key),
            timeout=config.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]
    except Exception as e:
        logger.error("[Agent] LLM call failed provider=%s: %s", provider, e)
        raise


# ---------------------------------------------------------------------------
# Agent 主循环
# ---------------------------------------------------------------------------

AGENT_MAX_ITERATIONS = 6  # 防止工具调用死循环


class AgentRunResult:
    def __init__(self):
        self.final_answer: str = ""
        self.messages_log: List[Dict] = []  # 完整对话轨迹（LLM + tool）
        self.tool_calls: List[Dict] = []    # 结构化工具调用记录（前端展示用）
        self.rag_used: List[Dict] = []
        self.iterations: int = 0
        self.response_time: float = 0.0
        self.token_usage: Dict[str, int] = {}


def run_agent(
    user_message: str,
    config,
    user_role: str = "viewer",
    user_role_name: str = "只读用户",
    session_history: Optional[List[Dict]] = None,
    memory_summary: str = "",
    rag_region=None,
) -> AgentRunResult:
    """
    执行一次 Agent 循环：
    1. 注入 system prompt（含角色上下文）
    2. 拼接历史对话
    3. LLM 返回 → 若 tool_calls 则执行 → 把结果塞回 messages → 再调 LLM
    4. 超过 AGENT_MAX_ITERATIONS 或 LLM 返回纯文本则结束
    """
    result = AgentRunResult()
    start = time.time()

    # 1. 构建 system prompt
    system_prompt = prompt_module.AGENT_SYSTEM_PROMPT + prompt_module.build_role_context(
        user_role, user_role_name
    )

    # 2. RAG 预检索（先按关键词拉一轮知识，作为初始上下文的一部分）
    rag_docs = retrieve_knowledge(user_message, top_k=4, region=rag_region)
    result.rag_used = rag_docs
    rag_prompt = prompt_module.build_rag_prompt(rag_docs)

    # 3. 初始化 messages
    messages: List[Dict] = [{"role": "system", "content": system_prompt}]
    history, memory = build_context(session_history or [], memory_summary, config.max_history)
    if memory:
        messages.append({"role": "system", "content": "【长期记忆（仅作个性化与连续性参考）】\n" + memory})
    messages.extend(history)

    user_content = user_message + rag_prompt
    messages.append({"role": "user", "content": user_content})
    result.messages_log.append({"role": "user", "content": user_message})

    # 4. 根据用户角色过滤可用工具
    all_tools = tool_module.get_tool_definitions()
    available_tools = perm_module.filter_tools_by_role(user_role, all_tools)
    tool_schemas = prompt_module.build_tool_descriptions(available_tools)

    logger.info("[Agent] start role=%s tools=%d query=%r", user_role, len(available_tools), user_message[:80])

    # 5. 主循环
    for iteration in range(1, AGENT_MAX_ITERATIONS + 1):
        result.iterations = iteration
        logger.info("[Agent] iteration %d", iteration)

        try:
            message = call_llm(messages, tool_schemas, config)
        except Exception as e:
            result.final_answer = f"AI 服务暂不可用：{e}"
            result.response_time = round(time.time() - start, 2)
            return result

        # 记录完整轨迹
        msg_entry = {"role": "assistant", "content": message.get("content") or ""}
        if message.get("tool_calls"):
            msg_entry["tool_calls"] = message["tool_calls"]
        messages.append(msg_entry)

        # 情况 A：模型直接返回文本（无 tool_calls）→ 结束
        if not message.get("tool_calls"):
            result.final_answer = message.get("content", "") or ""
            break

        # 情况 B：模型要求调用工具 → 逐个执行
        for tc in message["tool_calls"]:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}

            # 权限二次校验
            if not perm_module.can_use_tool(user_role, fn_name):
                tool_result = {
                    "success": False,
                    "tool": fn_name,
                    "summary": f"权限不足：角色 {user_role} 无权调用 {fn_name}",
                    "data": None,
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_simulated": True,
                }
            else:
                tool_result = tool_module.invoke_tool(fn_name, fn_args)

            # 记录到结果（前端展示用）
            result.tool_calls.append({
                "tool": fn_name,
                "arguments": fn_args,
                "summary": tool_result.get("summary", ""),
                "success": tool_result.get("success", True),
                "is_simulated": tool_result.get("is_simulated", False),
            })

            # 把 tool 结果追加到 messages，让模型继续
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": fn_name,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })

    else:
        # 超出迭代上限
        logger.warning("[Agent] max iterations reached")
        result.final_answer = "抱歉，我在处理您的请求时执行了太多步骤，请换一种方式描述您的问题。"

    result.response_time = round(time.time() - start, 2)
    logger.info("[Agent] done iter=%d time=%.2fs tools=%d",
                result.iterations, result.response_time, len(result.tool_calls))
    return result


# ---------------------------------------------------------------------------
# 降级：无 API key 时返回"模拟 Agent 回答"，保证前端不会空白
# ---------------------------------------------------------------------------

def run_agent_fallback(user_message: str, user_role: str = "viewer") -> AgentRunResult:
    """没有配置有效 LLM 时，用关键词匹配直接生成一个"看似像 Agent"的回答。"""
    result = AgentRunResult()
    result.response_time = 0.3
    result.iterations = 1

    msg = user_message.lower()

    if any(k in msg for k in ["水位", "液位", "水位线"]):
        tr = tool_module.tool_query_water_level()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = (
            f"【模拟回答】{tr['summary']}\n\n"
            + "\n".join(
                f"- {r['station_name']}：{r['current_level_m']}m（警戒 {r['alert_level_m']}m，{r['status']}）"
                for r in tr["data"]
            )
        )
    elif any(k in msg for k in ["流量", "过水"]):
        tr = tool_module.tool_query_flow_rate()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = f"【模拟回答】{tr['summary']}"
    elif any(k in msg for k in ["墒情", "土壤", "湿度"]):
        tr = tool_module.tool_query_soil_moisture()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = f"【模拟回答】{tr['summary']}"
    elif any(k in msg for k in ["天气", "气象", "气温", "下雨"]):
        tr = tool_module.tool_query_weather()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = f"【模拟回答】{tr['summary']}"
    elif any(k in msg for k in ["告警", "报警", "异常"]):
        tr = tool_module.tool_query_alerts()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = (
            f"【模拟回答】{tr['summary']}\n\n"
            + "\n".join(f"- [{r['level']}] {r['title']}：{r['message']}" for r in tr["data"])
        )
    elif any(k in msg for k in ["设备", "闸门", "水泵", "阀门"]):
        tr = tool_module.tool_device_status()
        result.tool_calls.append({"tool": tr["tool"], "summary": tr["summary"], "success": True})
        result.final_answer = f"【模拟回答】{tr['summary']}"
    elif any(k in msg for k in ["知识", "制度", "规定", "规范", "流程"]):
        docs = retrieve_knowledge(user_message, top_k=3)
        result.rag_used = docs
        if docs:
            result.final_answer = "\n".join(f"- [{d['title']}]({d['type']}): {d['summary'] or d['content'][:100]}"
                                            for d in docs)
        else:
            result.final_answer = "【模拟回答】知识库中暂未检索到相关内容。"
    else:
        result.final_answer = (
            "您好，我是**智渠**灌区管理智能体。我可以帮您：\n\n"
            "1. 🔍 查询**水位 / 流量 / 墒情 / 气象 / 水质**传感器数据\n"
            "2. ⚙️ 查看或**控制闸门、水泵、阀门**（需相应权限）\n"
            "3. 📖 检索灌区**管理制度、应急预案、操作规范**\n"
            "4. 📊 结合数据给出**灌溉调度建议、节水方案**\n\n"
            "当前处于【离线模拟模式】，请在后台配置有效的 AI 模型 API 后获得完整能力。"
        )

    return result
