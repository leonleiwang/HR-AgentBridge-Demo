import base64
import hmac
import json
import os
import time
import urllib.parse
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Tuple

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel

from demo_chat import demo_chat_html
from hr_demo import (
    ARTIFACT_DIR,
    candidate_card_html,
    candidate_to_dict,
    detect_task_type,
    get_artifact_path,
    get_candidate,
    report_html,
    result_to_dict,
    run_local_hr_demo,
    write_candidate_doc,
    write_candidate_html,
    write_compare_report,
)
from llm_client import call_qwen_hr_agent


load_dotenv()

DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "")
OPENCLAW_ENDPOINT = os.getenv("OPENCLAW_ENDPOINT", "")
OPENCLAW_TOKEN = os.getenv("OPENCLAW_TOKEN", "")
LLM_API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
USE_EXTERNAL_OPENCLAW = os.getenv("USE_EXTERNAL_OPENCLAW", "false").lower() == "true"


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(
    title="DianHR-AgentBridge",
    description="Multi-channel HR digital employee MVP for DingTalk, Feishu, OpenClaw, LLM, and local demo fallback.",
    version="0.2.0",
    default_response_class=UTF8JSONResponse,
)


class CallbackResponse(BaseModel):
    success: bool
    task_type: str
    source: str
    reply: str
    pushed_to_dingtalk: bool = False
    pushed_to_feishu: bool = False
    artifacts: Dict[str, str] = {}
    requires_confirmation: bool = False


def extract_text(payload: Dict[str, Any]) -> str:
    """Extract text from common DingTalk, Feishu, OpenClaw, and curl payloads."""
    text = payload.get("text")
    if isinstance(text, dict) and text.get("content"):
        return str(text["content"]).strip()
    if isinstance(text, str):
        return text.strip()

    if payload.get("content"):
        content = payload["content"]
        if isinstance(content, str):
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and parsed.get("text"):
                    return str(parsed["text"]).strip()
            except json.JSONDecodeError:
                return content.strip()
        return str(content).strip()

    event = payload.get("event")
    if isinstance(event, dict):
        message = event.get("message")
        if isinstance(message, dict):
            message_content = message.get("content")
            if isinstance(message_content, str):
                try:
                    parsed = json.loads(message_content)
                    if isinstance(parsed, dict) and parsed.get("text"):
                        return str(parsed["text"]).strip()
                except json.JSONDecodeError:
                    return message_content.strip()

    if payload.get("message"):
        return str(payload["message"]).strip()

    return str(payload).strip()


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
    sign = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
    separator = "&" if "?" in DINGTALK_WEBHOOK else "?"
    return f"{DINGTALK_WEBHOOK}{separator}timestamp={timestamp}&sign={sign}"


def push_to_dingtalk(reply: str) -> bool:
    if not DINGTALK_WEBHOOK:
        return False

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "DianHR 数字员工处理结果",
            "text": reply,
        },
    }

    try:
        response = requests.post(signed_dingtalk_webhook(), json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("errcode", 0) == 0
    except Exception as exc:
        print(f"[DingTalk Push Failed] {exc}")
        return False


def push_to_feishu(reply: str) -> bool:
    if not FEISHU_WEBHOOK:
        return False

    payload = {"msg_type": "text", "content": {"text": reply}}
    try:
        response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("code", 0) == 0 or data.get("StatusCode", 0) == 0
    except Exception as exc:
        print(f"[Feishu Push Failed] {exc}")
        return False


def call_external_openclaw(content: str) -> Tuple[Dict[str, Any], str]:
    headers = {"Content-Type": "application/json"}
    if OPENCLAW_TOKEN:
        headers["Authorization"] = f"Bearer {OPENCLAW_TOKEN}"

    payload = {
        "message": content,
        "task_type": detect_task_type(content),
        "constraints": {
            "high_risk_actions": "requires HR confirmation",
            "allowed_channels": ["dingtalk", "feishu", "api"],
            "allowed_tasks": [
                "recruitment_pipeline",
                "candidate_compare",
                "interview_email",
                "interview_evaluation",
                "onboarding",
                "policy_qa",
                "resume_screening",
            ],
        },
    }

    response = requests.post(OPENCLAW_ENDPOINT, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    reply = str(data.get("reply") or data.get("result") or data)
    return {
        "success": True,
        "task_type": data.get("task_type") or payload["task_type"],
        "source": "openclaw",
        "reply": reply,
        "artifacts": data.get("artifacts") or {},
        "requires_confirmation": "requires HR confirmation" in reply,
    }, "openclaw"


def run_hr_agent(content: str, channel: str = "api") -> Dict[str, Any]:
    if USE_EXTERNAL_OPENCLAW and OPENCLAW_ENDPOINT:
        try:
            result, source = call_external_openclaw(content)
            return result
        except Exception as exc:
            print(f"[OpenClaw Call Failed] {exc}")

    result = run_local_hr_demo(content)
    source = "local_demo"

    # For simple Q&A style tasks, allow a configured LLM to improve language while keeping safety boundaries.
    if result.task_type in {"policy_qa", "onboarding", "resume_screening"} and LLM_API_KEY and LLM_BASE_URL:
        llm_reply = call_qwen_hr_agent(result.task_type, content, "normal")
        if llm_reply:
            result.reply = f"{llm_reply}\n\n---\n\n本次回答由 LLM 生成；最终 HR 决策仍需人工确认。"
            source = "qwen_llm"

    data = result_to_dict(result, source)
    data["channel"] = channel
    return data


def response_from_result(data: Dict[str, Any], pushed_to_dingtalk: bool = False, pushed_to_feishu: bool = False) -> CallbackResponse:
    return CallbackResponse(
        success=True,
        task_type=data["task_type"],
        source=data["source"],
        reply=data["reply"],
        pushed_to_dingtalk=pushed_to_dingtalk,
        pushed_to_feishu=pushed_to_feishu,
        artifacts=data.get("artifacts") or {},
        requires_confirmation=bool(data.get("requires_confirmation")),
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "DianHR-AgentBridge", "version": "0.2.0"}


@app.get("/demo/chat")
def demo_chat() -> HTMLResponse:
    return HTMLResponse(demo_chat_html())


@app.get("/config")
def config() -> Dict[str, Any]:
    if USE_EXTERNAL_OPENCLAW and OPENCLAW_ENDPOINT:
        mode = "external_openclaw"
    elif LLM_API_KEY and LLM_BASE_URL:
        mode = "qwen_llm_with_local_artifacts"
    else:
        mode = "local_demo"

    return {
        "mode": mode,
        "channels": {
            "dingtalk_webhook": bool(DINGTALK_WEBHOOK),
            "feishu_webhook": bool(FEISHU_WEBHOOK),
        },
        "openclaw": {
            "enabled": USE_EXTERNAL_OPENCLAW,
            "endpoint": OPENCLAW_ENDPOINT or "not_configured",
        },
        "llm": {
            "configured": bool(LLM_API_KEY and LLM_BASE_URL),
            "base_url": LLM_BASE_URL or "not_configured",
            "model": LLM_MODEL,
        },
        "artifacts_dir": str(ARTIFACT_DIR),
    }


@app.post("/agent/run")
async def agent_run(request: Request) -> Dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    content = extract_text(payload)
    channel = str(payload.get("channel") or "api")
    return run_hr_agent(content, channel=channel)


@app.post("/dingtalk/callback", response_model=CallbackResponse)
async def dingtalk_callback(request: Request) -> CallbackResponse:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    content = extract_text(payload)
    data = run_hr_agent(content, channel="dingtalk")
    pushed = push_to_dingtalk(data["reply"])
    return response_from_result(data, pushed_to_dingtalk=pushed)


@app.post("/channels/dingtalk/callback", response_model=CallbackResponse)
async def channel_dingtalk_callback(request: Request) -> CallbackResponse:
    return await dingtalk_callback(request)


@app.post("/channels/feishu/callback", response_model=CallbackResponse)
async def feishu_callback(request: Request) -> CallbackResponse:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    content = extract_text(payload)
    data = run_hr_agent(content, channel="feishu")
    pushed = push_to_feishu(data["reply"])
    return response_from_result(data, pushed_to_feishu=pushed)


@app.get("/candidates/{candidate_id}")
def candidate_page(candidate_id: str) -> HTMLResponse:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    write_candidate_doc(candidate)
    write_candidate_html(candidate)
    return HTMLResponse(candidate_card_html(candidate))


@app.get("/api/candidates/{candidate_id}")
def candidate_api(candidate_id: str) -> Dict[str, Any]:
    candidate = get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate_to_dict(candidate)


@app.get("/reports/hrbp-compare")
def hrbp_compare_report() -> HTMLResponse:
    write_compare_report()
    return HTMLResponse(report_html())


@app.get("/artifacts/{filename}")
def artifact_file(filename: str) -> FileResponse:
    path = get_artifact_path(filename)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media_type = "text/markdown; charset=utf-8" if path.suffix == ".md" else None
    return FileResponse(path, media_type=media_type, filename=Path(filename).name)
