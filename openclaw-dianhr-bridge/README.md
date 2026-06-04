# OpenClaw DianHR Bridge

This is a minimal OpenClaw skill for routing DingTalk HR messages to the local
DianHR AgentBridge service.

Target service:

```text
POST http://127.0.0.1:8000/agent/run
```

Install on Windows:

```powershell
$src = "G:\MyProjects\Agent\HR_AgentBridge_Demo\openclaw-dianhr-bridge"
$dst = "$env:USERPROFILE\.openclaw\workspace\skills\dian-hr"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.openclaw\workspace\skills" | Out-Null
Copy-Item -Recurse -Force $src $dst
openclaw.cmd gateway restart
```

Test the bridge script directly:

```powershell
node "$env:USERPROFILE\.openclaw\workspace\skills\dian-hr\scripts\dianhr_bridge.mjs" --message "好久不见，请介绍下你自己"
```

Expected result: the output should start with the DianHR/HR-Insight greeting.

If OpenClaw still answers with the default agent, add this instruction to the
main agent/system prompt:

```text
所有来自钉钉或与 HR、招聘、候选人、简历、面试、offer、年假、考勤、薪资、入职相关的消息，必须使用 dian-hr skill。调用 bridge 脚本 POST 到 http://127.0.0.1:8000/agent/run，并将返回 JSON 的 reply 原样作为最终回复。不得用默认 Agent 自行回答。
```
