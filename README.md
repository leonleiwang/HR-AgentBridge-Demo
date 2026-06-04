# DianHR-AgentBridge

DianHR-AgentBridge is an HR digital employee demo for onsite presentation.

It keeps one HR Agent core and supports multiple channels:

```text
HR Agent Core
  |-- DingTalk channel: main live demo
  |-- Feishu channel: later enhancement / backup
  |-- OpenClaw adapter: optional external gateway
  |-- Local fallback: deterministic demo artifacts
```

The demo is not just Q&A. It shows an HR recruiting workflow:

- introduce the HR digital employee identity
- process candidate resumes
- generate candidate profiles
- compare candidates
- prepare interview email content
- generate a leadership-facing HTML report
- block high-risk HR decisions with `requires HR confirmation`

## Project Structure

```text
.
|-- app.py              # FastAPI service and channel/API endpoints
|-- hr_demo.py          # HR demo core, candidates, artifacts, HTML reports
|-- llm_client.py       # Qwen/DashScope OpenAI-compatible LLM fallback
|-- mock_dingtalk.py    # Mock DingTalk webhook receiver
|-- mock_openclaw.py    # Mock OpenClaw endpoint
|-- smoke_test.py       # Local verification script
|-- API_SPEC.md         # API contract and safety boundary
|-- DEMO_GUIDE.md       # Onsite demo script and fallback plan
|-- MAC_ONSITE_CHECKLIST.md # Mac setup, DingTalk/Qwen/OpenClaw checklist
|-- requirements.txt
|-- .env.example
```

## Quick Start

Windows:

```powershell
copy .env.example .env
D:\python\python.exe -m pip install -r requirements.txt
D:\python\python.exe run_demo_server.py
```

Mac:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_demo_server.py
```

Use `python -m uvicorn app:app --port 8000 --reload` only while actively developing.
For onsite demos, prefer `run_demo_server.py` because it does not restart when files change.

Open:

```text
http://localhost:8000/config
http://localhost:8000/demo/chat
http://localhost:8000/reports/hrbp-compare
```

## Local Smoke Test

```powershell
D:\python\python.exe smoke_test.py
```

Mac:

```bash
python3 smoke_test.py
```

Expected:

```text
Smoke test passed.
```

## Main API

```http
POST /agent/run
```

Example:

```json
{
  "message": "检查今天未读邮件里有没有新候选人简历，如果有就生成候选人档案和对比报告"
}
```

Important pages:

```text
http://localhost:8000/demo/chat
http://localhost:8000/candidates/liuchen
http://localhost:8000/candidates/wanglin
http://localhost:8000/reports/hrbp-compare
```

`/demo/chat` is only a local fallback UI. Use DingTalk as the primary onsite channel when the real channel is ready.

## Runtime Modes

Default local mode is stable for demos:

```env
USE_EXTERNAL_OPENCLAW=false
BASE_PUBLIC_URL=http://localhost:8000
```

To enable Qwen/DashScope for simple HR language generation:

```env
DASHSCOPE_API_KEY=your_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

To enable OpenClaw:

```env
USE_EXTERNAL_OPENCLAW=true
OPENCLAW_ENDPOINT=http://localhost:18789/agent/run
OPENCLAW_TOKEN=
```

Keep `USE_EXTERNAL_OPENCLAW=false` until the OpenClaw channel is verified. The local demo remains fully usable without it.

## Safety Boundary

The agent must not directly execute:

- final hiring decisions
- candidate rejection
- offer sending
- salary changes
- contract changes
- employee record changes
- permission changes

High-risk requests must include:

```text
requires HR confirmation
```

This boundary is part of the demo value. It shows that the digital employee assists HR rather than replacing HR authority.

## License

MIT License
