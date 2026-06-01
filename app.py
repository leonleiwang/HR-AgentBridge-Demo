import base64
import hmac
import os
import time
import urllib.parse
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from llm_client import call_qwen_hr_agent

# 架构说明：本文件是 HR 数字员工主服务，负责串起“钉钉入口 -> 任务路由 -> Agent Gateway -> LLM/Skill fallback -> Webhook 回推 -> 安全边界”。
# 钉钉入口：/dingtalk/callback 接收钉钉机器人或 curl 模拟的消息。
# 路由：根据用户文本识别简历初筛、入职流程、制度问答等 HR Skill。
# Agent Gateway：优先通过 OPENCLAW_ENDPOINT 调用外部 OpenClaw Gateway，证明外部 Agent Runtime 可替换接入。
# LLM/Skill fallback：没有 OpenClaw 时优先调用 Qwen；Qwen 不可用时回退到本地 HR Skill 模板。
# Webhook 回推：处理结果通过 DINGTALK_WEBHOOK 推回钉钉机器人或 Mock DingTalk。
# 安全边界：高风险 HR 动作不会直接执行，只返回 requires HR confirmation。
# 待接入点：真实企业数据、权限体系、审计日志、RAG 知识库、真实 HRIS/OA 工具执行器。

load_dotenv()

DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
OPENCLAW_ENDPOINT = os.getenv("OPENCLAW_ENDPOINT", "")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="DianHR-AgentBridge",
    description="HR digital employee MVP with DingTalk, OpenClaw, Qwen, and local fallback.",
    version="0.1.0",
    default_response_class=UTF8JSONResponse,
)


class CallbackResponse(BaseModel):
    success: bool
    task_type: str
    source: str
    reply: str
    pushed_to_dingtalk: bool


@dataclass
class HRTask:
    task_type: str
    content: str
    risk_level: str


HIGH_RISK_KEYWORDS = [
    "录用",
    "淘汰",
    "拒绝候选人",
    "发offer",
    "offer",
    "调薪",
    "降薪",
    "辞退",
    "解雇",
    "解除劳动合同",
    "修改薪资",
    "删除员工",
    "开除",
    "权限变更",
]

TASK_KEYWORDS = {
    "resume_screening": ["简历", "候选人", "筛选", "面试", "投递", "招聘"],
    "onboarding": ["入职", "onboarding", "报到", "工位", "账号", "新人"],
    "policy_qa": ["制度", "政策", "年假", "请假", "社保", "公积金", "加班", "报销", "福利"],
}


# 钉钉入口：从钉钉 callback 或 curl 模拟请求中提取用户消息文本。
def extract_dingtalk_text(payload: Dict[str, Any]) -> str:
    """Extract a message from common DingTalk robot callback shapes."""
    text = payload.get("text")
    if isinstance(text, dict):
        content = text.get("content")
        if content:
            return str(content).strip()

    if payload.get("msgtype") == "text" and isinstance(text, str):
        return text.strip()

    if payload.get("content"):
        return str(payload["content"]).strip()

    return str(payload).strip()


# 路由：根据关键词把自然语言请求分发到不同 HR Skill。
def detect_task_type(content: str) -> str:
    lowered = content.lower()
    for task_type, keywords in TASK_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            return task_type
    return "policy_qa"


# 安全边界：识别 offer、调薪、辞退、权限变更等高风险 HR 动作。
def detect_risk_level(content: str) -> str:
    lowered = content.lower()
    if any(keyword.lower() in lowered for keyword in HIGH_RISK_KEYWORDS):
        return "high"
    return "normal"


# 路由：构造标准 HRTask，后续 OpenClaw、Qwen、本地 Skill 都使用同一个任务契约。
def build_task(content: str) -> HRTask:
    return HRTask(
        task_type=detect_task_type(content),
        content=content,
        risk_level=detect_risk_level(content),
    )


# 安全边界：给高风险动作追加人工确认说明，避免 Demo 被理解成自动执行 HR 决策。
def risk_notice(task: HRTask) -> str:
    if task.risk_level != "high":
        return "- 当前任务未识别为高风险动作，但仍建议 HR 复核关键事实。"

    return (
        "- 检测到高风险 HR 动作，系统不会直接执行。\n"
        "- 输出内容仅作为分析和草稿，最终操作必须标记为：requires HR confirmation。"
    )


# 安全边界：无论 OpenClaw 或 LLM 返回什么，高风险任务最终都强制保留 requires HR confirmation。
def ensure_hr_confirmation(reply: str, task: HRTask) -> str:
    if task.risk_level != "high" or "requires HR confirmation" in reply:
        return reply

    return (
        f"{reply}\n\n---\n\n"
        "**强制风控标记：** requires HR confirmation。"
        "检测到高风险 HR 动作，系统不会直接执行。"
    )


# HR Skill：本地简历初筛模板；真实版本可接招聘系统、岗位 JD、面试评价和候选人库。
def run_resume_screening(task: HRTask) -> str:
    return f"""### 【HR数字员工：简历初筛】

**任务识别：** resume_screening

**候选信息：**
{task.content}

**初筛建议：**
- 根据岗位关键词提取候选人的技术栈、年限和项目匹配度。
- 如候选人具备目标岗位核心技能，可建议进入人工面试评估。
- 如信息不足，应补充项目经历、业务场景、稳定性和薪资期望。

**风险边界：**
{risk_notice(task)}

**需要 HR 人工确认：**
- 是否进入面试或淘汰候选人。
- 是否发送正式面试邀约、offer 或拒信。
"""


# HR Skill：本地入职流程清单模板；真实版本可接 HRIS、OA、账号权限、设备和工位流程。
def run_onboarding_checklist(task: HRTask) -> str:
    return f"""### 【HR数字员工：入职流程清单】

**任务识别：** onboarding

**入职信息：**
{task.content}

**清单建议：**
- 确认候选人身份信息、岗位、部门、入职日期和办公地点。
- 准备劳动合同、保密协议、员工手册签收材料。
- 创建邮箱、IM、OA、代码仓库或业务系统账号。
- 安排工位、电脑、门禁、直属经理和 Buddy。
- 入职首日安排公司介绍、制度说明和试用期目标沟通。

**风险边界：**
{risk_notice(task)}

**需要 HR 人工确认：**
- 合同版本、薪资福利、权限开通范围。
- 是否触发正式入职通知和系统账号创建。
"""


# HR Skill：本地制度问答模板；真实版本可接 RAG 知识库、员工手册、FAQ 和地区政策文档。
def run_policy_qa(task: HRTask) -> str:
    return f"""### 【HR数字员工：制度问答】

**任务识别：** policy_qa

**员工问题：**
{task.content}

**答复建议：**
- 先根据公司制度库确认适用范围，例如地区、员工类型、合同类型和入职年限。
- 对年假、请假、社保、公积金、加班、报销等问题，给出原则性说明和办理入口。
- 如果问题涉及劳动争议、医疗隐私、薪酬调整或处分，应转 HR 专员处理。

**风险边界：**
{risk_notice(task)}

**需要 HR 人工确认：**
- 涉及个人薪酬、劳动关系、纪律处分、医疗隐私的答复。
- 与现行制度冲突或员工信息不完整的情况。
"""


# LLM/Skill fallback：本地 HR Skill 兜底，保证没有外部模型和网关时 Demo 仍可运行。
def run_local_hr_agent(task: HRTask) -> str:
    skills = {
        "resume_screening": run_resume_screening,
        "onboarding": run_onboarding_checklist,
        "policy_qa": run_policy_qa,
    }
    handler = skills.get(task.task_type, run_policy_qa)
    return handler(task)


# LLM/Skill fallback：没有 OpenClaw 时优先走 Qwen；Qwen 不可用时自动回退本地 Skill。
def run_hr_digital_employee(task: HRTask) -> tuple[str, str]:
    llm_result = call_qwen_hr_agent(task.task_type, task.content, task.risk_level)
    if llm_result:
        reply = f"""### 【HR数字员工 - Qwen模式】

{llm_result}

---

**系统说明：** 当前结果由 Qwen LLM 生成。高风险动作不会自动执行，必须 requires HR confirmation。
"""
        return ensure_hr_confirmation(reply, task), "qwen"

    reply = f"""### 【HR数字员工 - Mock模式】

{run_local_hr_agent(task)}

---

**系统说明：** 当前未调用外部 LLM，使用本地 HR Skill 模板回退。
"""
    return ensure_hr_confirmation(reply, task), "local_mock"


# Agent Gateway：如果配置 OPENCLAW_ENDPOINT，就通过 HTTP 调用外部 OpenClaw Gateway。
# 待接入点：真实 OpenClaw 可在这里连接企业工具执行器、审批流、审计日志和权限校验。
def call_openclaw_agent(task: HRTask) -> tuple[str, str]:
    if not OPENCLAW_ENDPOINT:
        return run_hr_digital_employee(task)

    headers = {"Content-Type": "application/json"}
    if OPENCLAW_TOKEN:
        headers["Authorization"] = f"Bearer {OPENCLAW_TOKEN}"

    payload = {
        "message": task.content,
        "task_type": task.task_type,
        "risk_level": task.risk_level,
        "constraints": {
            "high_risk_actions": "requires HR confirmation",
            "allowed_tasks": ["resume_screening", "onboarding", "policy_qa"],
        },
    }

    try:
        response = requests.post(
            OPENCLAW_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        reply = data.get("reply") or data.get("result") or str(data)
        return ensure_hr_confirmation(str(reply), task), "openclaw"
    except Exception as exc:
        print(f"[OpenClaw Call Failed] {exc}")
        fallback_reply, fallback_source = run_hr_digital_employee(task)
        reply = f"""### 【HR数字员工 - OpenClaw失败后回退】

**OpenClaw 调用失败：** {exc}

{fallback_reply}
"""
        return ensure_hr_confirmation(reply, task), f"openclaw_failed_to_{fallback_source}"


# Webhook 回推：按钉钉机器人安全签名规则为真实 DingTalk Webhook 生成签名 URL。
def signed_dingtalk_webhook() -> str:
    if not DINGTALK_SECRET:
        return DINGTALK_WEBHOOK

    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}"
    digest = hmac.new(
        DINGTALK_SECRET.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        digestmod=sha256,
    ).digest()
    sign = urllib.parse.quote_plus(
        base64.b64encode(digest).decode("utf-8")
    )
    separator = "&" if "?" in DINGTALK_WEBHOOK else "?"
    return f"{DINGTALK_WEBHOOK}{separator}timestamp={timestamp}&sign={sign}"


# Webhook 回推：把 HR Agent 结果发送到 Mock DingTalk 或真实 DingTalk 机器人。
def push_to_dingtalk(reply: str) -> bool:
    if not DINGTALK_WEBHOOK:
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "HR数字员工处理结果",
            "text": reply,
        },
    }

    try:
        response = requests.post(
            signed_dingtalk_webhook(),
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("errcode", 0) == 0
    except Exception as exc:
        print(f"[DingTalk Push Failed] {exc}")
        return False


# 健康检查：用于演示服务已启动，也方便未来接入监控系统。
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "DianHR-AgentBridge"}


# 配置检查：展示当前处于 OpenClaw、Qwen 还是本地 mock 模式，证明外部接入点可替换。
# 待接入点：生产环境可在这里增加权限体系、租户配置、审计开关和知识库索引状态。
@app.get("/config")
def config() -> Dict[str, Any]:
    if OPENCLAW_ENDPOINT:
        mode = "external_openclaw"
    elif LLM_API_KEY and LLM_BASE_URL:
        mode = "qwen_llm"
    else:
        mode = "local_mock"

    return {
        "dingtalk_webhook": bool(DINGTALK_WEBHOOK),
        "openclaw_endpoint": OPENCLAW_ENDPOINT or "local_agent",
        "llm_base_url": LLM_BASE_URL or "not_configured",
        "llm_model": LLM_MODEL,
        "llm_configured": bool(LLM_API_KEY and LLM_BASE_URL),
        "mode": mode,
    }


# 钉钉入口：主回调接口，模拟钉钉用户消息进入 HR 数字员工。
# 主链路：入口 -> 路由 -> Agent Gateway -> LLM/Skill fallback -> Webhook 回推 -> 安全边界。
@app.post("/dingtalk/callback", response_model=CallbackResponse)
async def dingtalk_callback(request: Request) -> CallbackResponse:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    content = extract_dingtalk_text(payload)
    task = build_task(content)

    reply, source = call_openclaw_agent(task)
    pushed = push_to_dingtalk(reply)

    return CallbackResponse(
        success=True,
        task_type=task.task_type,
        source=source,
        reply=reply,
        pushed_to_dingtalk=pushed,
    )


# Agent API：给外部系统或未来 OpenClaw 反向调用本地 HR Agent 的标准接口。
# 待接入点：可在这里接真实企业数据、RAG 检索、HRIS/OA 工具执行器和审计日志。
@app.post("/agent/run")
async def run_agent(request: Request) -> Dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    content = str(payload.get("message") or payload.get("content") or "")
    task = build_task(content)
    reply, source = run_hr_digital_employee(task)
    return {
        "success": True,
        "task_type": task.task_type,
        "source": source,
        "reply": reply,
    }
