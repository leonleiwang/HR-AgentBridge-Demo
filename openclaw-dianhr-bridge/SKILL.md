---
name: dian-hr
description: Route DingTalk HR messages to the local DianHR AgentBridge service and return its reply.
---

# DianHR Bridge

Use this skill for all HR-related messages, especially messages received from
DingTalk. Do not answer those messages with the default general agent when this
skill is available.

The local HR service is:

```text
POST http://127.0.0.1:8000/agent/run
```

Request body:

```json
{"message":"user message"}
```

The service response contains `reply`. Return `reply` as the final chat reply.

## Required Behavior

When the user asks about recruitment, candidates, resumes, interviews, offers,
leave, attendance, salary, onboarding, HR policy, or HR decision support:

1. Call the bridge script with the original user message.
2. Return the script output directly.
3. Do not add extra commentary before or after the returned HR reply.

Use this command:

```powershell
node "{baseDir}/scripts/dianhr_bridge.mjs" --message "<original user message>"
```

If the local HR service is unavailable, return exactly:

```text
DianHR 本地服务暂时不可用，请确认 http://127.0.0.1:8000/health 是否正常。
```

## Safety Boundary

For offer, hiring, rejection, salary, sensitive employee data, or permission
changes, the local service may mark the action as requiring HR confirmation.
Preserve that warning. Never present the result as a final HR decision.
