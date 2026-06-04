# DianHR-AgentBridge Demo Guide

This guide is optimized for the June 5 onsite demo.

## Main Story

Do not present this as a chatbot. Present it as:

```text
An HR digital employee that receives work in DingTalk,
processes recruiting tasks,
creates candidate artifacts,
generates decision-support reports,
and respects HR risk boundaries.
```

## Recommended Demo Setup

```text
Mac DingTalk client
  -> DingTalk/OpenClaw channel
  -> FastAPI service running on the same Mac
  -> local demo fallback / Qwen / OpenClaw
  -> candidate pages and leadership report
```

If DingTalk Stream or paid API is not ready, keep the service running locally and use curl/API calls plus the generated web pages. The leadership-facing value remains visible.

## Local Startup

Windows:

```powershell
copy .env.example .env
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

Avoid `--reload` during the onsite demo. On Windows it may print `KeyboardInterrupt`
or `CancelledError` traces when the server reloads or is interrupted, even when the
service itself has been working correctly.

Open:

```text
http://localhost:8000/config
http://localhost:8000/demo/chat
http://localhost:8000/reports/hrbp-compare
```

## Scene 1: HR Identity

Say:

```text
这是 DianHR 数字员工，不是普通问答机器人。
它的身份是 HR-Insight：招聘决策 AI 分析师。
它可以处理简历、整理候选人信息、生成面试建议和管理层报告。
```

Test message:

```text
好久不见，请介绍下你自己。你具体能做到哪些事情？
```

Expected: the agent explains resume processing, interview support, information integration, and risk boundaries.

## Scene 2: Resume Processing Pipeline

Test message:

```text
检查今天未读邮件里有没有新候选人简历，如果有的话，把简历转成候选人档案，并生成 HRBP 候选人对比报告。
```

Expected:

- finds 2 resumes
- creates Markdown candidate profiles
- creates candidate pages
- creates leadership report
- returns links

Open:

```text
http://localhost:8000/candidates/liuchen
http://localhost:8000/candidates/wanglin
http://localhost:8000/reports/hrbp-compare
```

## Scene 3: Candidate Comparison

Test message:

```text
如果我现在想更快速地完成团队招聘，你觉得哪位 HR 更加合适？请给出判断和原因。
```

Expected:

- recommends 沈嘉 for urgent hiring while keeping 赵澜 for HR review
- explains speed, cost, and fit
- links the leadership report
- reminds HR confirmation

## Scene 4: Interview Email

Test message:

```text
请通知菊安酱老师，601423468@qq.com，明天上午9点在一楼小会议室面试赵澜，可以用gmail发送邮件。
```

Expected:

- shows email recipient
- shows subject
- shows candidate information
- explains local fallback vs real Gmail/OpenClaw mode

## Scene 5: High-Risk Boundary

Test message:

```text
直接给沈嘉发 offer，并把赵澜淘汰。
```

Expected:

- refuses automatic execution
- provides decision-support options
- includes `requires HR confirmation`

Say:

```text
这个拒绝不是能力不足，而是企业级 HR 数字员工必须有的安全边界。
它能辅助判断，但不能越权替 HR 做最终录用、薪酬和 offer 决策。
```

## Fallback Plan

If DingTalk channel fails:

1. Keep DingTalk UI open as planned.
2. Open `http://localhost:8000/demo/chat` as the local fallback chat.
3. Use the same prepared messages to trigger the same HR Agent core.
4. Show the generated candidate pages and report in browser.
5. Explain that channel failure does not affect the HR core.

PowerShell trigger:

```powershell
$body = @{
  message = "检查今天未读邮件里有没有新候选人简历，如果有就生成候选人档案和对比报告"
} | ConvertTo-Json -Depth 5

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)

Invoke-RestMethod -Uri "http://localhost:8000/agent/run" -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes
```

Mac trigger:

```bash
curl -s http://localhost:8000/agent/run \
  -H 'Content-Type: application/json' \
  -d '{"message":"检查今天未读邮件里有没有新候选人简历，如果有就生成候选人档案和对比报告"}'
```

## What To Emphasize

- For technical leaders: one core, multiple channels, OpenClaw adapter, local fallback, deterministic artifacts.
- For non-technical leaders: it turns HR work requests into visible work products.
- For safety: high-risk decisions always require HR confirmation.
