# DianHR-AgentBridge API Spec

This project keeps one HR Agent core and exposes it through multiple channels.

```text
HR Agent Core
  |-- DingTalk channel: main live demo
  |-- Feishu channel: later enhancement / backup channel
  |-- OpenClaw adapter: optional external gateway
  |-- Local demo fallback: deterministic artifact generation
```

## Runtime Modes

| Mode | Env | Behavior |
|---|---|---|
| local_demo | `USE_EXTERNAL_OPENCLAW=false` | Generates HR artifacts locally. Works offline except optional webhooks. |
| qwen_llm_with_local_artifacts | `LLM_BASE_URL` + API key | Uses local artifacts, and lets LLM improve simple Q&A/onboarding replies. |
| external_openclaw | `USE_EXTERNAL_OPENCLAW=true` + `OPENCLAW_ENDPOINT` | Sends tasks to OpenClaw first, then falls back locally if it fails. |

## Core Endpoint

### `POST /agent/run`

Used by OpenClaw, DingTalk adapters, Feishu adapters, curl, or tests.

Request:

```json
{
  "channel": "api",
  "message": "检查今天未读邮件里有没有新候选人简历，如果有就生成候选人档案和对比报告"
}
```

Response:

```json
{
  "success": true,
  "task_type": "recruitment_pipeline",
  "source": "local_demo",
  "reply": "Markdown reply for IM clients",
  "artifacts": {
    "候选人对比报告": "http://localhost:8000/reports/hrbp-compare"
  },
  "requires_confirmation": true,
  "generated_at": "2026-06-04T00:00:00+00:00",
  "channel": "api"
}
```

## Channel Endpoints

### `POST /dingtalk/callback`

Backward-compatible DingTalk style endpoint.

Accepted shapes:

```json
{
  "text": {
    "content": "帮我处理新候选人简历"
  }
}
```

```json
{
  "msgtype": "text",
  "text": "帮我处理新候选人简历"
}
```

### `POST /channels/dingtalk/callback`

Same as `/dingtalk/callback`, kept for the new multi-channel structure.

### `POST /channels/feishu/callback`

Accepts Feishu-like event payloads and generic text payloads.

```json
{
  "event": {
    "message": {
      "content": "{\"text\":\"帮我处理新候选人简历\"}"
    }
  }
}
```

## Artifact Endpoints

### `GET /candidates/liuchen`

HTML candidate profile for 沈嘉. The route keeps the old id for compatibility.

### `GET /candidates/wanglin`

HTML candidate profile for 赵澜. The route keeps the old id for compatibility.

### `GET /reports/hrbp-compare`

Offline-capable HTML leadership report. It uses built-in browser Canvas only; no CDN is required.

### `GET /artifacts/{filename}`

Download generated Markdown or HTML files from `ARTIFACT_DIR`.

## Safety Boundary

The agent must not directly execute:

- final hiring decisions
- candidate rejection
- offer sending
- salary changes
- contract changes
- employee record changes
- permission changes

When such tasks are detected, the response must include:

```text
requires HR confirmation
```

This is intentional and should be shown in the demo as a trust signal.
