# DianHR-AgentBridge

HR-AgentBridge 是一个数字员工集成 Demo，暂时设定这名数字员工的身份是 HR。

它的目标不是做完整生产系统，而是证明一条可落地的企业数字员工链路：通过 OpenClaw 一类的 Agent Gateway / 企业智能助手运行时，连接钉钉等办公协同入口，接收员工或 HR 的自然语言请求，路由到 HR 场景能力，并把处理结果回推到聊天窗口。

当前版本用 FastAPI、Mock DingTalk、Mock OpenClaw、Qwen 接入位和本地 HR Skill fallback，演示“可接入、可替换、可扩展”的最小闭环。

## 核心链路

```text
钉钉消息 / curl 模拟
        |
        v
FastAPI 主服务
        |
        +--> HR 任务识别与风险判断
        |
        +--> OpenClaw Gateway 适配点
        |
        +--> Qwen LLM / 本地 HR Skill fallback
        |
        v
钉钉 Webhook 回推
```

## 已实现能力

- 钉钉风格消息入口：`/dingtalk/callback`
- OpenClaw Gateway 适配点：`OPENCLAW_ENDPOINT`
- Qwen / DashScope OpenAI-compatible API 接入
- 本地 HR Skill fallback
- Mock DingTalk Webhook 回推
- `/health` 和 `/config` 演示接口
- 高风险 HR 动作人工确认边界

当前内置三个 HR 场景：

- 简历初筛
- 入职流程清单
- HR 制度问答

高风险动作不会直接执行，例如发 offer、最终录用或淘汰、调薪、辞退、修改员工档案、权限变更等，系统会返回：

```text
requires HR confirmation
```

## 项目结构

```text
.
├── app.py              # 主服务：入口、路由、OpenClaw/Qwen/local fallback、Webhook 回推
├── llm_client.py       # Qwen / DashScope OpenAI-compatible API 客户端
├── mock_openclaw.py    # Mock OpenClaw Gateway
├── mock_dingtalk.py    # Mock DingTalk Webhook
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## 快速开始

安装依赖：

```powershell
cd "G:\MyProjects\Agent\HR_AgentBridge_Demo"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

复制配置：

```powershell
copy .env.example .env
```

本地演示推荐 `.env`：

```env
DASHSCOPE_API_KEY=
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

DINGTALK_WEBHOOK=http://localhost:9100/robot/send
DINGTALK_SECRET=

OPENCLAW_ENDPOINT=http://localhost:9000/agent/run
OPENCLAW_TOKEN=demo-token
```

## 启动演示

打开三个 PowerShell 终端。

终端 1：Mock OpenClaw。

```powershell
uvicorn mock_openclaw:app --port 9000
```

终端 2：Mock DingTalk。

```powershell
uvicorn mock_dingtalk:app --port 9100
```

终端 3：主服务。

```powershell
uvicorn app:app --port 8000 --reload
```

如果 8000 被占用，可以换成 8010：

```powershell
uvicorn app:app --port 8010 --reload
```

检查配置：

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/config"
```

看到 `mode : external_openclaw` 表示当前正在通过 OpenClaw 适配点演示外部 Agent Gateway 模式。

## 演示请求

PowerShell 推荐用 UTF-8 bytes 发送，避免中文乱码。

```powershell
$body = @{
  text = @{
    content = "办理入职：张三，AI工程师，2026年6月10日入职，杭州总部"
  }
} | ConvertTo-Json -Depth 5

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)

Invoke-RestMethod -Uri "http://localhost:8000/dingtalk/callback" -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes
```

预期结果：

```text
success            : True
task_type          : onboarding
source             : openclaw
pushed_to_dingtalk : True
```

Mock DingTalk 终端会打印收到的回推消息。

## 面试说明

可以这样介绍：

```text
这是一个 HR 数字员工 MVP，不是完整生产系统。
我重点证明的是工程链路：办公入口、任务路由、Agent Gateway、LLM/Skill fallback、Webhook 回推和安全边界。

真实上线时，Mock DingTalk 可以替换成真实钉钉机器人，
Mock OpenClaw 可以替换成企业部署的 OpenClaw Gateway，
本地 Skill 和 Qwen Prompt 可以接入企业知识库、人力资源信息系统、办公自动化审批系统、招聘系统和审批流。
```

后续可扩展方向：

- 企业制度、员工手册和 FAQ 的 RAG 知识库
- 招聘系统、候选人库和岗位 JD
- 人力资源信息系统和办公自动化审批系统工具执行器
- 权限体系、审计日志、数据脱敏和合规控制
- 高风险动作审批流

## License

MIT License
