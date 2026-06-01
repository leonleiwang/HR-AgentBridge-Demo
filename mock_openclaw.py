from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# 架构说明：本文件是 Mock OpenClaw Gateway，用真实 HTTP 服务模拟外部 Agent Gateway。
# Agent Gateway：主服务配置 OPENCLAW_ENDPOINT 后会调用这里，证明以后可替换成企业真实 OpenClaw。
# 安全边界：Mock 只返回建议和 Markdown 结果，高风险动作仍标记为 requires HR confirmation。
# 待接入点：真实 OpenClaw 可接 HRIS/OA 工具执行器、审批流、权限体系、审计日志和企业数据源。


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(title="Mock OpenClaw Gateway", default_response_class=UTF8JSONResponse)


# 健康检查：用于确认 Mock OpenClaw Gateway 已启动。
@app.get("/health")
def health():
    return {"status": "ok", "service": "Mock OpenClaw Gateway"}


# Agent Gateway：模拟 OpenClaw 接收 HR Agent 任务并返回结构化执行结果。
@app.post("/agent/run")
async def run_agent(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    message = body.get("message", "")
    task_type = body.get("task_type", "unknown")
    risk_level = body.get("risk_level", "normal")

    return {
        "reply": f"""### 【OpenClaw Mock 执行结果】

已收到 HR Agent 任务。

**任务类型：**
{task_type}

**任务内容：**
{message}

**执行策略：**
1. 只执行低风险 HR 辅助任务
2. 高风险动作转人工确认
3. 返回结构化 Markdown 结果

**风险等级：**
{risk_level}

**需要 HR 人工确认：**
{"requires HR confirmation" if risk_level == "high" else "关键事实和最终操作建议由 HR 复核"}

**状态：**
OpenClaw Gateway 调用成功。
"""
    }
