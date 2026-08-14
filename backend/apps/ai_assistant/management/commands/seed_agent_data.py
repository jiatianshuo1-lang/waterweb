"""
初始化 Agent 所需的种子数据：
1. 创建默认 DeepSeek AI 配置（已禁用，等待用户填 API key 启用）
2. 预置灌区知识库条目（制度、预案、FAQ）
3. 可选：创建一个 admin + viewer 测试用户

用法：python manage.py seed_agent_data
     python manage.py seed_agent_data --reset   # 先清空再重建知识库
"""

from django.core.management.base import BaseCommand
from apps.ai_assistant.models import AiAssistantConfig, AiKnowledge


DEFAULT_AI_CONFIG = {
    "name": "智渠 Agent (DeepSeek)",
    "provider": "deepseek",
    "model_name": "deepseek-chat",
    "api_url": "",
    "api_key": "",
    "system_prompt": "",
    "temperature": 0.7,
    "max_tokens": 2048,
    "max_history": 10,
    "timeout": 30,
    "is_active": False,
    "description": "默认 Agent 配置（DeepSeek 模型），请在后台填写 API Key 后启用",
}


KNOWLEDGE_SEED = [
    {
        "title": "灌区供水调度管理制度",
        "knowledge_type": "policy",
        "summary": "规范灌区供水调度的计划制定、执行、监控和调整流程",
        "tags": ["供水", "调度", "制度", "管理"],
        "content": (
            "第一章 总则\n"
            "第一条 为规范灌区供水调度管理，保障供水安全和高效，根据国家和地方相关法规，制定本制度。\n"
            "第二条 本制度适用于灌区范围内的水库、渠道、泵站、闸门等水利工程的供水调度。\n"
            "\n"
            "第二章 计划制定\n"
            "第三条 每年 10 月编制下一年度供水计划，根据来水预测、种植结构、用水需求综合平衡。\n"
            "第四条 供水计划须经灌区管理处审核后报上级主管部门审批。\n"
            "\n"
            "第三章 调度执行\n"
            "第五条 供水调度实行分级负责制，重要调度指令由调度中心统一发布。\n"
            "第六条 闸门操作须严格执行'先开下游、后开上游'的原则，防止渠道冲刷。\n"
            "\n"
            "第四章 应急处置\n"
            "第七条 当遇突发停水、设备故障等情况，应立即启动应急预案，同时上报主管部门。"
        ),
    },
    {
        "title": "闸门远程操作规程",
        "knowledge_type": "procedure",
        "summary": "闸门远程控制的标准操作流程和注意事项",
        "tags": ["闸门", "远程控制", "操作", "自动化"],
        "content": (
            "1. 操作前确认：检查设备在线状态、上下游水位、目标开度是否合理。\n"
            "2. 手动/自动模式切换：远程操作前须确认现场无人作业，模式切换后等待 30 秒。\n"
            "3. 开度调整：每次调整步长不超过 15%，两次调整间隔不少于 3 分钟。\n"
            "4. 执行确认：操作指令发出后观察设备状态反馈，连续 3 次无响应视为异常。\n"
            "5. 应急停机：发现异常立即发送 close_gate 指令，同时通知运维人员到现场。\n"
            "\n"
            "安全红线：严禁在暴雨、雷电天气进行远程操作；严禁越权操作非管辖区域闸门。"
        ),
    },
    {
        "title": "干旱应急预案",
        "knowledge_type": "emergency",
        "summary": "灌区干旱分级响应和处置措施",
        "tags": ["干旱", "应急", "抗旱", "预警"],
        "content": (
            "干旱预警分为四级：\n"
            "• 蓝色预警（轻度干旱）：土壤含水率 18-22%，启动节水灌溉模式，加强墒情监测。\n"
            "• 黄色预警（中度干旱）：土壤含水率 14-18%，启动应急供水方案，优先保障口粮田，限制非农业用水。\n"
            "• 橙色预警（重度干旱）：土壤含水率 10-14%，跨区域调水，实行限时供水，组织抗旱服务队。\n"
            "• 红色预警（特大干旱）：土壤含水率 <10%，启动应急水源，上报上级抗旱指挥部，必要时组织人工送水。\n"
            "\n"
            "应急措施：\n"
            "1. 优先开启深层井灌设备\n"
            "2. 调整灌溉计划为夜间灌溉（减少蒸发）\n"
            "3. 组织巡检队排查管网漏损\n"
            "4. 协调气象部门开展人工增雨"
        ),
    },
    {
        "title": "灌溉水质标准",
        "knowledge_type": "document",
        "summary": "农田灌溉水质国家标准（GB 5084）主要指标",
        "tags": ["水质", "标准", "灌溉", "GB5084"],
        "content": (
            "根据《农田灌溉水质标准》GB 5084-2021：\n\n"
            "• pH 值：5.5 - 8.5\n"
            "• 悬浮物：≤ 100 mg/L（水作）、≤ 80 mg/L（旱作）\n"
            "• 化学需氧量：≤ 300 mg/L（水作）、≤ 200 mg/L（旱作）\n"
            "• 总氮：≤ 30 mg/L\n"
            "• 总磷：≤ 10 mg/L\n"
            "• 水温：≤ 35℃\n"
            "• 浊度：≤ 100 NTU\n\n"
            "超出标准时应：\n"
            "1. 溯源排查污染源\n"
            "2. 启动应急净化措施\n"
            "3. 通知受影响农户\n"
            "4. 上报环保和水利主管部门"
        ),
    },
    {
        "title": "智能灌溉触发条件说明",
        "knowledge_type": "faq",
        "summary": "智能灌溉系统常见触发条件解释",
        "tags": ["智能灌溉", "触发", "自动化", "FAQ"],
        "content": (
            "Q: 智能灌溉是怎么自动启动的？\n"
            "A: 系统支持三种触发方式：\n"
            "   ① 墒情触发：当 0-40cm 平均含水率低于设定阈值（一般 18-20%）\n"
            "   ② 时间触发：按设定的时间表定时启动\n"
            "   ③ 气象触发：结合天气预报，在降雨前 12 小时不启动灌溉\n\n"
            "Q: 为什么有时墒情到阈值了却没启动？\n"
            "A: 常见原因：\n"
            "   • 灌溉计划处于暂停状态\n"
            "   • 设备离线或故障\n"
            "   • 系统判断近期有降雨（气象预报降水概率 > 60%）\n"
            "   • 当日已完成灌溉时长\n\n"
            "Q: 灌溉时长是怎么算的？\n"
            "A: 根据作物类型、土壤类型、当前含水率和目标含水率综合计算，公式为：\n"
            "   灌溉量(m³/亩) = (目标含水率 - 当前含水率) × 土壤容重 × 计划湿润层深度 × 666.7"
        ),
    },
    {
        "title": "量测水数据异常排查指南",
        "knowledge_type": "procedure",
        "summary": "量测水测站数据异常的常见原因和排查步骤",
        "tags": ["量测水", "故障排查", "传感器", "运维"],
        "content": (
            "一、数据不更新（测站离线）\n"
            "  1. 检查供电：太阳能板是否被遮挡、电池电压是否正常\n"
            "  2. 检查通讯：天线连接、信号强度（建议 > -80dBm）\n"
            "  3. 重启设备：断电 30 秒后重新上电\n\n"
            "二、数据跳变异常\n"
            "  1. 传感器探头是否接触良好\n"
            "  2. 测量窗口是否有杂物遮挡\n"
            "  3. 检查是否有强电磁干扰源\n\n"
            "三、数据偏低或偏高\n"
            "  1. 与人工观测对比校验\n"
            "  2. 检查传感器是否需要校准（建议每年一次）\n"
            "  3. 确认水位/流量计算参数是否正确\n\n"
            "四、紧急联系\n"
            "  设备故障超过 24 小时未恢复 → 上报运维主管\n"
            "  关键数据缺失影响调度决策 → 启动人工巡测应急预案"
        ),
    },
    {
        "title": "灌区节水管理制度",
        "knowledge_type": "policy",
        "summary": "灌区节水政策、用水定额和奖惩措施",
        "tags": ["节水", "政策", "定额", "水价"],
        "content": (
            "一、用水定额\n"
            "  • 小麦：350-450 m³/亩/季\n"
            "  • 玉米：280-380 m³/亩/季\n"
            "  • 水稻：500-650 m³/亩/季\n"
            "  • 蔬菜：300-500 m³/亩/季\n\n"
            "二、阶梯水价\n"
            "  • 基础定额内：按 0.15 元/m³\n"
            "  • 超定额 0-20%：加价 50%\n"
            "  • 超定额 20% 以上：加价 100%\n\n"
            "三、节水奖励\n"
            "  实际用水量低于定额 10% 以上的用水户，给予节水奖励（0.05 元/m³）\n\n"
            "四、违规处理\n"
            "  • 擅自改装计量设备：责令改正 + 罚款\n"
            "  • 拖欠水费超过 30 天：限制供水\n"
            "  • 恶意破坏水利设施：移交司法机关"
        ),
    },
    {
        "title": "防洪应急预案",
        "knowledge_type": "emergency",
        "summary": "灌区汛期防洪调度和险情处置预案",
        "tags": ["防洪", "汛期", "应急", "水库"],
        "content": (
            "一、汛前准备（每年 5 月前完成）\n"
            "  1. 水库大坝、涵闸、渠道全面排查\n"
            "  2. 防汛物资储备（编织袋、铅丝、砂石料、救生衣）\n"
            "  3. 预警通讯系统测试\n"
            "  4. 防汛队伍组建和演练\n\n"
            "二、分级响应\n"
            "  • 蓝色（24h 降雨 50mm）：加强值守，水位加密监测（每 1 小时）\n"
            "  • 黄色（24h 降雨 100mm）：预泄腾库，通知下游做好准备\n"
            "  • 橙色（24h 降雨 150mm）：启动分洪预案，组织危险区群众转移\n"
            "  • 红色（24h 降雨 250mm）：全面抗洪，请求外部支援\n\n"
            "三、险情处置\n"
            "  • 管涌：围井反滤，减少渗压\n"
            "  • 滑坡：削坡减载，锚固加固\n"
            "  • 漫溢：加高加固，紧急泄洪"
        ),
    },
]


class Command(BaseCommand):
    help = "初始化 Agent 种子数据：AI 配置 + 灌区知识库"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="清空现有知识库后重建（不影响已存在的会话和日志）",
        )

    def handle(self, *args, **options):
        self.stdout.write("==> 初始化 Agent 种子数据")

        # 1. AI 配置
        cfg, created = AiAssistantConfig.objects.update_or_create(
            name=DEFAULT_AI_CONFIG["name"],
            defaults=DEFAULT_AI_CONFIG,
        )
        action = "创建" if created else "更新"
        self.stdout.write(self.style.SUCCESS(f"[{action}] AI 配置: {cfg.name} (provider={cfg.provider}, model={cfg.model_name})"))

        # 2. 知识库
        if options["reset"]:
            deleted, _ = AiKnowledge.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"已清空全部知识库条目（{deleted} 条）"))

        for item in KNOWLEDGE_SEED:
            obj, created = AiKnowledge.objects.get_or_create(
                title=item["title"],
                defaults=item,
            )
            status = "+" if created else "="
            self.stdout.write(f"  [{status}] {item['knowledge_type']} {item['title'][:30]}")

        total = AiKnowledge.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\n完成！知识库共 {total} 条"))
        self.stdout.write("提示：请在后台管理页面填写 DeepSeek API Key 并将配置标记为 is_active=True")
