from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# 架构说明：本文件是 Mock DingTalk Webhook，用真实 HTTP 服务模拟钉钉机器人接收回推消息。
# Webhook 回推：主服务配置 DINGTALK_WEBHOOK 后会把 HR Agent 结果发送到这里。
# 演示价值：即使没有真实钉钉，也能证明“处理结果推回聊天入口”的链路已经跑通。
# 待接入点：生产环境把 DINGTALK_WEBHOOK 换成真实钉钉机器人地址，并增加企业鉴权和审计日志。


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


app = FastAPI(title="Mock DingTalk Webhook", default_response_class=UTF8JSONResponse)


# 健康检查：用于确认 Mock DingTalk Webhook 已启动。
@app.get("/health")
def health():
    return {"status": "ok", "service": "Mock DingTalk Webhook"}


# Webhook 回推：接收主服务推送来的 Markdown 消息，并打印到终端用于现场演示。
@app.post("/robot/send")
async def send_message(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {exc}") from exc

    print("\n====== Mock DingTalk Received ======")
    print(body)
    print("====================================\n")

    return {
        "errcode": 0,
        "errmsg": "ok",
    }
