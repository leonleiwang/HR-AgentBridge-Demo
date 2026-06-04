# Mac Onsite Checklist

This checklist is for running the HR-Insight demo from a Mac after pulling the
GitHub repository.

## Recommended Path

Use the local fallback first. It does not require DingTalk, Qwen, or OpenClaw to
be ready, and it still demonstrates the same HR Agent core, candidate pages, and
HRBP report.

```bash
git clone https://github.com/leonleiwang/HR-AgentBridge-Demo.git
cd HR-AgentBridge-Demo
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 smoke_test.py
python3 run_demo_server.py
```

Open these pages:

```text
http://localhost:8000/config
http://localhost:8000/demo/chat
http://localhost:8000/reports/hrbp-compare
```

## Optional Qwen Setup

Qwen is optional for this demo. The deterministic local HR workflow works
without it. If richer natural-language replies are needed, manually edit `.env`:

```env
DASHSCOPE_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3-max
```

Useful official links:

- API Key: https://help.aliyun.com/zh/model-studio/get-api-key
- Qwen API reference: https://help.aliyun.com/zh/model-studio/qwen-api-reference/
- Model pricing: https://help.aliyun.com/zh/model-studio/model-pricing

Notes:

- The API Key must be created by the Alibaba Cloud main account, or by a RAM
  user with the required API-Key page permission.
- `qwen3-max` is stronger, but `qwen-plus` is cheaper and enough for basic
  Q&A. The built-in artifact flow is local either way.
- Do not commit `.env` or API keys.

## DingTalk Setup

For a real live chat channel, prefer an enterprise internal robot/application
that can receive messages and call this FastAPI service. A custom group robot
Webhook is useful for outbound notifications, but it is not the main receiving
channel for this demo.

Official links:

- Robot overview: https://open.dingtalk.com/document/development/development-robot-overview
- Custom robot access: https://open.dingtalk.com/document/orgapp/custom-robot-access
- Custom robot Webhook address: https://open.dingtalk.com/document/dingstart/obtain-the-webhook-address-of-a-custom-robot
- Server API overview: https://open.dingtalk.com/document/development/api-overview

`.env` fields already supported by this repo:

```env
DINGTALK_WEBHOOK=
DINGTALK_SECRET=
BASE_PUBLIC_URL=http://localhost:8000
```

If DingTalk must call the Mac from outside the local machine, expose the Mac
service through a temporary HTTPS tunnel and set:

```env
BASE_PUBLIC_URL=https://your-public-demo-url
```

Then point the DingTalk callback or integration layer to:

```text
https://your-public-demo-url/dingtalk/callback
```

## OpenClaw Setup

OpenClaw is optional. Keep it disabled until the channel is verified:

```env
USE_EXTERNAL_OPENCLAW=false
```

If OpenClaw is ready, enable it only after confirming the gateway endpoint:

```env
USE_EXTERNAL_OPENCLAW=true
OPENCLAW_ENDPOINT=http://localhost:18789/agent/run
OPENCLAW_TOKEN=
```

Official OpenClaw guide:

- https://help.aliyun.com/zh/model-studio/openclaw

For OpenClaw model payment, the official guide supports Token Plan, Coding Plan,
and pay-as-you-go. The pay-as-you-go path uses an Alibaba Cloud Model Studio API
Key (`sk-xxxxx`) and the regional DashScope/OpenClaw base URL shown in the
OpenClaw documentation.

## Demo Fallback

If DingTalk or OpenClaw is not stable onsite:

1. Keep the DingTalk client visible as the intended channel.
2. Open `http://localhost:8000/demo/chat`.
3. Use the side conversation panel to trigger the same HR Agent core.
4. Show `http://localhost:8000/reports/hrbp-compare` as the business artifact.
5. Explain that the channel is replaceable, while the HR workflow and safety
   boundary are the core value.
